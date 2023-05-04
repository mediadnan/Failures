import importlib
from typing import List

from pytest import fixture

import failures
from failures import Failure


class FailureHolder:
    failures: List[Failure]

    def __init__(self):
        self.failures = []

    def __call__(self, failure: Failure) -> None:
        self.failures.append(failure)

    @property
    def sources(self) -> List[str]:
        return [failure.source for failure in self.failures]

    @property
    def errors(self) -> List[Exception]:
        return [failure.error for failure in self.failures]


@fixture
def handler() -> FailureHolder:
    """Object that stores the failure when called"""
    return FailureHolder()


@fixture
def error():
    """Generic exception made available for testing"""
    return Exception("Test error")
