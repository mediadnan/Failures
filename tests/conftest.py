import sys
import importlib
import unittest.mock
from typing import Optional

from pytest import fixture

import failures


class FailureHolder:
    source: Optional[str]
    error: Optional[Exception]

    def __init__(self):
        self.source = None
        self.error = None

    def __call__(self, source: str, error: Exception) -> None:
        self.source = source
        self.error = error


@fixture
def handler():
    return FailureHolder()


@fixture
def no_colorama_dependency():
    modules_copy = sys.modules.copy()
    modules_copy.pop("colorama")
    with unittest.mock.patch.object(sys, "modules", modules_copy):
        try:
            importlib.reload(failures)
            yield
        finally:
            importlib.reload(failures)


@fixture
def error():
    return Exception("Test error")
