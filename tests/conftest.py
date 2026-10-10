import os
import sys
from pathlib import Path

TESTS_DIR = Path(os.path.dirname(__file__))
sys.path.append(str(TESTS_DIR.parent))
sys.path.append(str(TESTS_DIR))


def pytest_addoption(parser):
    parser.addoption('--update-snapshots', action='store_true', default=False, help='Rewrite card snapshots with the current card outputs')
