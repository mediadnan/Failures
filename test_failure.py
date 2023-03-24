import logging
import pytest
from failures import Reporter, NORMAL


def fail():
    raise Exception("This is a test exception")


def test_reporter_root_defaults():
    reporter = Reporter('root')
    assert reporter.name == 'root'
    assert reporter.details == {}
    assert reporter.severity is NORMAL
