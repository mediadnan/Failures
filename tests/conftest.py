from typing import Tuple, List

from pytest import fixture


class FailureHolder:
    failures: List[Tuple[str, Exception]]

    def __init__(self):
        self.failures = []

    def __call__(self, source: str, error: Exception) -> None:
        self.failures.append((source, error))

    @property
    def sources(self) -> List[str]:
        return [src for src, _ in self.failures]

    @property
    def errors(self) -> List[Exception]:
        return [failure for _, failure in self.failures]


@fixture
def handler():
    return FailureHolder()


@fixture
def error():
    return Exception("Test error")
