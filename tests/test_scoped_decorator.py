import pytest
import failures


@pytest.mark.parametrize("decorator, source", [
    pytest.param('failures.scoped', 'test.my_function', id="unparametrized"),
    pytest.param('failures.scoped()', 'test.my_function', id="empty_parenthesis"),
    pytest.param('failures.scoped(name="my_func")', 'test.my_func', id="custom_name"),
    pytest.param('failures.scoped(handler=handler)', 'my_function', id="custom_local_handler"),
    pytest.param('failures.scoped(name="my_func", handler=handler)', 'my_func', id="custom_name_and_handler"),
])
def test_scoped_decorator_configurations(error, handler, decorator: str, source: str):
    @eval(decorator)
    def my_function(_item, *, _something: bool = True) -> None:
        raise error
    with failures.scope('test', handler):
        my_function(5)
    assert handler.failures == [(source, error)]


def test_uncompromised_decorated_info():
    from inspect import getfullargspec, signature
    from typing import Tuple

    def my_func(_first: int, /, _second: str, *_args, _third: bool, **_kwargs) -> Tuple[int, int, bool]:
        """This is a test documentation"""
    decorated = failures.scoped(my_func)
    assert my_func.__name__ == decorated.__name__
    assert my_func.__doc__ == decorated.__doc__
    assert my_func.__annotations__ == decorated.__annotations__
    assert my_func.__kwdefaults__ == decorated.__kwdefaults__
    assert my_func.__defaults__ == decorated.__defaults__
    assert getfullargspec(my_func) == getfullargspec(decorated)
    assert signature(my_func) == signature(decorated)


def test_unsupported_decorated_class():
    with pytest.raises(TypeError, match="failures.scoped only supports decorating standard functions"):
        @failures.scoped
        class CallableObject:
            def __call__(self, *args, **kwargs):
                pass


def test_invalid_param_validation():
    with pytest.raises(TypeError, match="failures.scoped only supports decorating standard functions"):
        failures.scoped(object())   # noqa
