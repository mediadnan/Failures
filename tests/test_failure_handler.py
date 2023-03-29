import importlib
import re
import sys
from importlib import import_module

import pytest
from unittest import mock

# noinspection PyProtectedMember
from failures.handler import Failure, print_failure, _error_format  # noqa: W0212


def test_failure_exception(error):
    failure = Failure("inner", error)
    assert failure.source == "inner"
    assert failure.error is error
    failure = failure.within("inside")
    assert failure.source == "inside.inner"
    assert failure.error is error
    failure = failure.within("outer")
    assert failure.source == "outer.inside.inner"
    assert failure.error is error


MESSAGE_PATTERN = re.compile(
    r".*\[FAILURE].*test_source.*::.*ValueError\(.*test error.*\).*\d{4}-\d\d-\d\d \d\d:\d\d:\d\d.*"
)


def test_print_failure_format_with_colorama_installed():
    assert MESSAGE_PATTERN.match(
        _error_format.format(src="test_source", type="ValueError", error="test error", time="2023-06-21 05:25:30")
    )


@pytest.mark.xfail()
def test_print_failure_format_without_colorama_installed(no_colorama_dependency):
    from importlib import reload
    import failures
    with mock.patch.dict(sys.modules, {'colorama': None}):
        reload(failures.handler)
        message = failures.handler._error_format.format(
            src="test_source", type="ValueError", error="test error", time="2023-06-21 05:25:30"
        )
    reload(failures.handler)
    assert message == "[FAILURE] test_source :: ValueError(test error) 2023-06-21 05:25:30"


def test_print_failure(capsys):
    print_failure("test_source", ValueError("test error"))
    captured = capsys.readouterr()
    assert MESSAGE_PATTERN.match(captured.out)
