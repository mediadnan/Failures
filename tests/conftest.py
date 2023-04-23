from typing import List

from pytest import fixture, param
from failures import Failure, Severity


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

    @property
    def severities(self) -> List[Severity]:
        return [failure.severity for failure in self.failures]


@fixture
def handler() -> FailureHolder:
    return FailureHolder()


@fixture
def error():
    return Exception("Test error")


def pytest_generate_tests(metafunc):
    """Automatically parametrizes tests for common tests"""
    if "valid_label" in metafunc.fixturenames:
        metafunc.parametrize("valid_label", [
            "root",
            "root.sub",
            "root.sub_scope",
            "root.sub.sub.sub",
            "root.scope1",
            "scope2",
            "scope.iteration[5].func",
            "scope.func(1)",
        ])
    if all(fixt in metafunc.fixturenames for fixt in ("invalid_label", "err_type", "err_msg")):
        metafunc.parametrize("invalid_label,err_type,err_msg", [
            param(object(), TypeError, "label must be a string", id="wrong_type_name"),
            param(b'name.sub', TypeError, "label must be a string", id="wrong_type_name_bytes"),
            param('', ValueError, "invalid label: ''", id="empty_name"),
            param('name..sub', ValueError, "invalid label: 'name..sub'", id="double_dot"),
            param('.name', ValueError, "invalid label", id="leading_dot"),
            param('name.', ValueError, "invalid label", id="trailing_dot"),
        ])
