from failures.context import handle, scope


def test_flat_error_handling(handler, error):
    with handle("testing", handler):
        raise error
    assert handler.error is error
    assert handler.source == "testing"


def test_suppress_failures(handler, error):
    with handle("testing", None):
        raise error
    assert handler.error is None
    assert handler.source is None


def test_wrapped_error_handling(handler, error):
    with handle("testing", handler):
        with scope("function"):
            raise error
    assert handler.error is error
    assert handler.source == "testing.function"


def test_supress_error_handling(handler, error):
    with handle("testing", None):
        with scope("function"):
            raise error
    assert handler.error is None
    assert handler.source is None
