import re
import sys
import importlib

import pytest

import failures


@pytest.fixture
def no_colorama_installed(monkeypatch):
    modules_copy = sys.modules.copy()
    modules_copy.pop("colorama")
    monkeypatch.setattr(sys, "modules", modules_copy)
    importlib.reload(failures.handler)


def test_failure_exception(error):
    failure = failures.context.Failure("inner", error)
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
    pattern = failures.handler._error_format
    assert MESSAGE_PATTERN.match(
        pattern.format(src="test_source", type="ValueError", error="test error", time="2023-06-21 05:25:30")
    )


@pytest.mark.xfail()
def test_print_failure_format_without_colorama_installed(no_colorama_installed):
    message = failures.handler._error_format.format(
        src="test_source", type="ValueError", error="test error", time="2023-06-21 05:25:30"
    )
    assert message == "[FAILURE] test_source :: ValueError(test error) 2023-06-21 05:25:30"


def test_print_failure(capsys):
    failures.handler.print_failure("test_source", ValueError("test error"))
    captured = capsys.readouterr()
    assert MESSAGE_PATTERN.match(captured.out)
