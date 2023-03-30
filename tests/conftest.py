from typing import Tuple, List

from pytest import fixture


class FailureHolder:
    failures: List[Tuple[str, Exception]]

    def __init__(self):
        self.failures = []

    def __call__(self, source: str, error: Exception) -> None:
        self.failures.append((source, error))


@fixture
def handler():
    return FailureHolder()


@fixture
def error():
    return Exception("Test error")
