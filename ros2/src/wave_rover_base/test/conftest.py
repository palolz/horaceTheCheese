"""Conftest to prevent FastDDS C++ atexit hang on macOS after ROS 2 tests finish."""

import os


def pytest_sessionfinish(session, exitstatus):
    os._exit(int(exitstatus))
