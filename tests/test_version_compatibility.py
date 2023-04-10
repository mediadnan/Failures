import pytest
import failures


def test_flat_error_handling(handler, error):
    # ensures compatibility with v0.1
    with failures.handle("testing", handler):
        raise error
    assert handler.failures == [("testing", error)]


def test_suppress_failures(handler, error):
    # ensures compatibility with v0.1
    with failures.handle("testing", handler, ignore=Exception):
        raise error
    assert handler.failures == []


def test_suppress_specific_failures(handler):
    # ensures compatibility with v0.1
    type_error = TypeError("type error")
    value_error = ValueError("value error")
    with failures.handle("root", handler, ignore=ValueError) as inner_scope:
        with inner_scope("value_err"):
            raise value_error
        with inner_scope("type_err"):
            raise type_error
    assert handler.failures == [("root.type_err", type_error)]


def test_wrapped_error_handling(handler, error):
    # ensures compatibility with v0.1
    with failures.handle("testing", handler):
        with failures.scope("function"):
            raise error
    assert handler.failures == [("testing.function", error)]


def test_nested_scopes_handling(handler, error):
    # ensures compatibility with v0.1
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
    # ensures compatibility with v0.1
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
    # ensures compatibility with v0.1
    with failures.handle("testing", handler):
        with failures.scope("inner_scope"):
            pass
    assert not handler.failures


def test_successful_bound_scope_execution(handler):
    # ensures compatibility with v0.1
    with failures.handle("testing", handler) as scope:
        with scope:
            pass
    assert not handler.failures


def test_successful_multiple_bound_scope_execution(handler):
    # ensures compatibility with v0.1
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
    # ensures compatibility with v0.1
    with pytest.raises(BaseException):
        with failures.handle("testing", handler):
            with failures.scope("inner_scope"):
                raise BaseException("test_exception")  # noqa


def test_higher_exception_propagation_bound_scope(handler):
    # ensures compatibility with v0.1
    with pytest.raises(BaseException):
        with failures.handle("testing", handler) as scope:
            with scope("inner_scope"):
                raise BaseException("test_exception")  # noqa


def test_handle_without_handler():
    # ensures compatibility with v0.1
    with pytest.raises(failures.Failure):
        with failures.handle("testing", None):
            with failures.scope("scope"):
                raise Exception("test_exception")


def test_invalid_handler_type():
    with pytest.raises(TypeError, match="Failure handler must be a callable"):
        failures.handle("root_handler", object())  # noqa


def test_valid_names_handle(valid_label: str, handler):
    # ensures compatibility with v0.1
    failures.handle(valid_label, handler)


def test_invalid_names_handle(invalid_label, err_type, err_msg, handler):
    # ensures compatibility with v0.1
    with pytest.raises(err_type, match=err_msg):
        failures.handle(invalid_label, handler)


def test_supress_error_handling(handler, error):
    # ensures compatibility with v0.1
    with failures.handle("testing", handler, ignore=Exception):
        with failures.scope("function"):
            raise error
    assert handler.failures == []


def test_failures_deprecated_add(error):
    # ensures compatibility with v0.1
    from failures.core import Failures, Failure
    fls = Failures(Failure('failure1', error), Failure('failure2', error))
    with pytest.warns(DeprecationWarning):
        fls.add(Failure('failure3', error))
