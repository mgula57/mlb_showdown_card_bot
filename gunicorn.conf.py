"""Gunicorn settings for the web dyno.

The sim runner is a background thread living inside these worker processes (see
`mlb_showdown_bot/api/sim.py`), so worker lifecycle *is* sim lifecycle: anything that kills a
worker kills every simulation running in it, mid-phase, with no chance to record why. The
settings here exist mostly to stop that from happening.
"""

import os

# Set before the app is imported under `preload_app`, so `app.py` knows to skip its eager
# connection-pool warm-up: pools created in the master are discarded by each child after the
# fork (they are not fork-safe), making the master's copies pure waste. `post_fork` below warms
# them per worker instead, which is where they are actually used.
os.environ['GUNICORN_PRELOAD'] = '1'

# gthread, not the default sync worker. A sync worker only heartbeats to the arbiter *between*
# requests, so any single request slower than `timeout` gets the whole process SIGKILLed - taking
# every in-flight sim thread in it down as collateral. gthread heartbeats from its own loop
# independently of what the request threads are doing.
worker_class = 'gthread'

# Two workers, not three: each can run `_MAX_CONCURRENT_SIMS` CPU-bound simulations, and the dyno
# has far less CPU (and RAM) to share out than a dev machine. Fewer, less contended workers finish
# sims faster than more workers thrashing.
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


def post_fork(server, worker):
    """Give each worker its own database connections.

    psycopg2 connections cannot be shared across a fork - two processes on one socket interleave
    and corrupt the protocol stream. Under `preload_app` the children inherit whatever the master
    opened at import time, so they must drop those (without closing them, which would break the
    master's copy) and build their own.
    """
    from mlb_showdown_bot.core.database.postgres_db import _discard_pools_after_fork, _get_pool

    _discard_pools_after_fork()
    _get_pool('DATABASE_URL_LOGS')
    _get_pool('DATABASE_URL_ARCHIVE')
