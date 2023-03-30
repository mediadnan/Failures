from failures.context import scope, handle


def test_flat_error_handling(handler, error):
    with handle("testing", handler):
        raise error
    assert handler.failures == [("testing", error)]


def test_suppress_failures(handler, error):
    with handle("testing", handler, ignore=Exception):
        raise error
    assert handler.failures == []


def test_suppress_specific_failures(handler):
    type_error = TypeError("type error")
    value_error = ValueError("value error")
    with handle("root", handler, ignore=ValueError) as inner_scope:
        with inner_scope("value_err"):
            raise value_error
        with inner_scope("type_err"):
            raise type_error
    assert handler.failures == [("root.type_err", type_error)]


def test_wrapped_error_handling(handler, error):
    with handle("testing", handler):
        with scope("function"):
            raise error
    assert handler.failures == [("testing.function", error)]


def test_supress_error_handling(handler, error):
    with handle("testing", handler, ignore=Exception):
        with scope("function"):
            raise error
    assert handler.failures == []


def test_nested_scopes_handling(handler, error):
    with handle("testing", handler) as root_scope:
        with root_scope("first") as first_scope:
            with first_scope("inner"):
                raise error
            raise error
        with root_scope("second"):
            raise error
        raise error
    failures = [src for src, _ in handler.failures]
    assert failures == ["testing.first.inner", "testing.first", "testing.second", "testing"]
