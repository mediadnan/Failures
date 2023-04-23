import pytest
import failures
from inspect import getfullargspec, signature
from failures import FailureException


@pytest.mark.parametrize("decorator, source", [
    pytest.param('failures.scoped', 'my_function', id="unparametrized"),
    pytest.param('failures.scoped()', 'my_function', id="empty_parenthesis"),
    pytest.param('failures.scoped(name="my_func")', 'my_func', id="custom_name"),
])
def test_scoped_decorator_configurations(error, handler, decorator: str, source: str):
    @eval(decorator)
    def my_function(_item, *, _something: bool = True) -> None:
        raise error
    try:
        my_function(5)
    except FailureException as fe:
        assert fe.source == source
        assert fe.error is error


def _compare_wrapper_and_wrapped(func):
    decorated = failures.scoped(func)
    assert func.__name__ == decorated.__name__
    assert func.__doc__ == decorated.__doc__
    assert func.__annotations__ == decorated.__annotations__
    assert func.__kwdefaults__ == decorated.__kwdefaults__
    assert func.__defaults__ == decorated.__defaults__
    assert getfullargspec(func) == getfullargspec(decorated)
    assert signature(func) == signature(decorated)


def test_uncompromised_decorated_info():
    def my_func(_first: int, /, _second: str, *_args, _third: bool, **_kwargs) -> int:
        """This is a test documentation"""
    _compare_wrapper_and_wrapped(my_func)
