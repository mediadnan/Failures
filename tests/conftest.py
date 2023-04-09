import typing
import pytest


class FailureHolder:
    failures: typing.List[typing.Tuple[str, Exception]]

    def __init__(self):
        self.failures = []

    def __call__(self, source: str, error: Exception) -> None:
        self.failures.append((source, error))

    @property
    def sources(self) -> typing.List[str]:
        return [src for src, _ in self.failures]

    @property
    def errors(self) -> typing.List[Exception]:
        return [failure for _, failure in self.failures]


@pytest.fixture
def handler():
    return FailureHolder()


@pytest.fixture
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
            pytest.param(object(), TypeError, "label must be a string", id="wrong_type_name"),
            pytest.param(b'name.sub', TypeError, "label must be a string", id="wrong_type_name_bytes"),
            pytest.param('', ValueError, "invalid label: ''", id="empty_name"),
            pytest.param('name..sub', ValueError, "invalid label: 'name..sub'", id="double_dot"),
            pytest.param('.name', ValueError, "invalid label", id="leading_dot"),
            pytest.param('name.', ValueError, "invalid label", id="trailing_dot"),
        ])
