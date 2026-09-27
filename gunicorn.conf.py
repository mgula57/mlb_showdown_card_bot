"""Gunicorn settings for the web dyno.

The sim runner is a background thread living inside these worker processes (see
`mlb_showdown_bot/api/sim.py`), so worker lifecycle *is* sim lifecycle: anything that kills a
worker kills every simulation running in it, mid-phase, with no chance to record why. The
settings here exist mostly to stop that from happening.
"""

import ctypes
import ctypes.util
import os

# Set before the app is imported under `preload_app`, so `app.py` knows to skip its eager
# connection-pool warm-up: pools created in the master are discarded by each child after the
# fork (they are not fork-safe), making the master's copies pure waste. `post_fork` below warms
# them per worker instead, which is where they are actually used.
os.environ['GUNICORN_PRELOAD'] = '1'

# The app imports `supabase` lazily, on first upload. Every web worker uploads (each card build
# does), so import it here in the master instead: forked workers then share one copy-on-write
# instead of each importing a private ~40 MB of it after the fork.
import supabase  # noqa: E402,F401

# gthread, not the default sync worker. A sync worker only heartbeats to the arbiter *between*
# requests, so any single request slower than `timeout` gets the whole process SIGKILLed - taking
# every in-flight sim thread in it down as collateral. gthread heartbeats from its own loop
# independently of what the request threads are doing.
worker_class = 'gthread'

# One sim per worker (`SIM_MAX_CONCURRENT=1`), so this is the dyno's concurrent-sim capacity: a
# sim is CPU-bound and holds the GIL, so parallelism has to come from processes, not threads.
# Sized for a 1 GB Standard-2X: a sim peaks ~170 MB above an idle worker, and a worker keeps ~100 MB
# of that afterward. Check `internal.sim_job.memory` before raising it further.
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
threads = int(os.environ.get('WEB_THREADS', 4))

# Comfortably above the worst case for the routes that call the MLB Stats API, whose client
# retries three times against a 30s socket timeout (~93s). The old default of 30s meant a single
# slow upstream call killed a worker and all of its sims.
timeout = 120

# Long enough for an in-flight request to drain on a dyno restart. Sims are daemon threads and die
# regardless - `_install_shutdown_handler` in api/sim.py is what marks their rows failed.
graceful_timeout = 30

# Heroku's router already sits in front of this and closes idle connections at 55s.
keepalive = 5

# Forking after the app is imported shares the interpreter's pages copy-on-write, which is a real
# saving on a 512MB dyno with pandas/Pillow/pydantic loaded. Requires everything import-time to be
# fork-safe - see `post_fork`.
preload_app = True

# Recycle workers periodically so a slow leak in a long-lived process can't accumulate into an
# R14. Jittered so both workers never recycle at the same moment.
max_requests = 800
max_requests_jitter = 200

accesslog = '-'
errorlog = '-'


# glibc `mallopt` params (malloc.h). Linux-only; `_libc` stays None elsewhere (e.g. macOS dev).
_M_MMAP_THRESHOLD = -3
_M_ARENA_MAX = -8
_libc = ctypes.CDLL(ctypes.util.find_library('c')) if hasattr(ctypes.CDLL(None), 'mallopt') else None


def _tune_malloc():
    """Stop card-image buffers from lingering in the worker after a request.

    Pillow frees image blocks (up to 16 MB each; a full card layer is ~12.6 MB) straight back to
    malloc. glibc's default mmap threshold is adaptive: the first such free raises it to that
    block size, so every later image lands in a heap arena instead, where fragmentation keeps it
    from ever being returned to the OS. Pinning the threshold keeps large buffers on mmap, which
    are unmapped the moment they're freed. Capping arenas stops each gthread thread from growing
    its own heap.
    """
    if _libc is None:
        return
    _libc.mallopt(_M_MMAP_THRESHOLD, 1024 * 1024)
    _libc.mallopt(_M_ARENA_MAX, 2)


def post_request(worker, req, environ, resp):
    """Hand freed-but-retained heap pages back to the OS after each request."""
    if _libc is not None:
        _libc.malloc_trim(0)


def post_fork(server, worker):
    """Give each worker its own database connections.

    psycopg2 connections cannot be shared across a fork - two processes on one socket interleave
    and corrupt the protocol stream. Under `preload_app` the children inherit whatever the master
    opened at import time, so they must drop those (without closing them, which would break the
    master's copy) and build their own.
    """
    from mlb_showdown_bot.core.database.postgres_db import _discard_pools_after_fork, _get_pool

    _tune_malloc()
    _discard_pools_after_fork()
    _get_pool('DATABASE_URL_LOGS')
    _get_pool('DATABASE_URL_ARCHIVE')
