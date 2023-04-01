from typing import Tuple, Type, Callable, Any

import pytest

import failures


# use cases
def test_flat_error_handling(handler, error):
    with failures.handle("testing", handler):
        raise error
    assert handler.failures == [("testing", error)]


def test_suppress_failures(handler, error):
    with failures.handle("testing", handler, ignore=Exception):
        raise error
    assert handler.failures == []


def test_suppress_specific_failures(handler):
    type_error = TypeError("type error")
    value_error = ValueError("value error")
    with failures.handle("root", handler, ignore=ValueError) as inner_scope:
        with inner_scope("value_err"):
            raise value_error
        with inner_scope("type_err"):
            raise type_error
    assert handler.failures == [("root.type_err", type_error)]


def test_wrapped_error_handling(handler, error):
    with failures.handle("testing", handler):
        with failures.scope("function"):
            raise error
    assert handler.failures == [("testing.function", error)]


def test_supress_error_handling(handler, error):
    with failures.handle("testing", handler, ignore=Exception):
        with failures.scope("function"):
            raise error
    assert handler.failures == []


def test_nested_scopes_handling(handler, error):
    with failures.handle("testing", handler) as scope:
        with scope("first") as first_scope:
            with first_scope("inner"):
                raise error
            raise error
        with scope("second"):
            raise error
        raise error
    assert handler.sources == ["testing.first.inner", "testing.first", "testing.second", "testing"]


def test_nested_in_scope_error_handling(handler, error):
    with failures.handle("testing", handler) as scope:
        try:
            raise error  # some error occurs
            name = "unreachable"  # noqa
        except Exception as err:
            scope.add_failure(err, "getting_name")
            name = "unset"  # mimics alternative code
    assert name, "Name should be set in either cases"
    assert handler.sources == ["testing.getting_name"]


def test_successful_unbound_scope_execution(handler):
    with failures.handle("testing", handler):
        with failures.scope("inner_scope"):
            pass
    assert not handler.failures


def test_successful_bound_scope_execution(handler):
    with failures.handle("testing", handler) as scope:
        with scope:
            pass
    assert not handler.failures


def test_successful_multiple_bound_scope_execution(handler):
    with failures.handle("testing", handler) as scope:
        try:
            pass
        except Exception as err:
            scope.add_failure(err, "test_1")
            return
        try:
            pass
        except Exception as err:
            scope.add_failure(err, "test_2")
            return
    assert not handler.failures


def test_higher_exception_propagation_unbound_scope(handler):
    with pytest.raises(BaseException):
        with failures.handle("testing", handler):
            with failures.scope("inner_scope"):
                raise BaseException("test_exception")  # noqa


def test_higher_exception_propagation_bound_scope(handler):
    with pytest.raises(BaseException):
        with failures.handle("testing", handler) as scope:
            with scope("inner_scope"):
                raise BaseException("test_exception")  # noqa


# validation
@pytest.mark.parametrize("handled", [True, False], ids=["with_handler", "without_handler"])
@pytest.mark.parametrize(
    "func", [
        pytest.param(failures.scope, id="scope"),
        pytest.param(failures.handle, id="handle"),
        pytest.param(failures.scope('root'), id="sub_scope"),
    ]
    )
@pytest.mark.parametrize(
    "name,err_type,err_msg", [
        pytest.param(object(), TypeError, "name must be a string", id="wrong_type_name"),
        pytest.param('', ValueError, "invalid name: ''", id="empty_name"),
        pytest.param('root-handler', ValueError, "invalid name: 'root-handler'", id="hyphen_name"),
    ]
    )
def test_unhandled_name_validation_error(
        handler,
        name: str,
        err_type: [Type[BaseException], Tuple[Type[BaseException], ...]],
        err_msg: str,
        func: Callable[[str], Any],
        handled: bool
):
    with pytest.raises(err_type, match=err_msg):
        if handled:
            with failures.handle('testing', handler):
                func(name)
        else:
            func(name)


def test_scope_add_error_without_label(error):
    with pytest.raises(ValueError, match="The error must be labeled"):
        failures.scope('testing').add_failure(error)  # noqa
    scope = failures.scope('testing')
    scope.add_failure(failures.Failure("test_src", error))
    assert scope._failures
    with pytest.raises(TypeError, match="Invalid error type {object}"):
        failures.scope('testing').add_failure(object()) # noqa


def test_duplicate_name_sub_scope():
    scope = failures.scope("root_scope")
    scope("sub_sub")
    with pytest.raises(ValueError, match="The name 'sub_sub' is already used in this scope"):
        scope("sub_sub")


def test_invalid_handler_type():
    with pytest.raises(TypeError, match="Failure handler must be a callable"):
        failures.handle("root_handler", object())   # noqa
