from contextlib import nullcontext as is_ok
from pytest import mark, raises, param
from failures import Handler, print_failure, Failure, Not


@mark.parametrize("args, expectation", [
    ("()", is_ok()),
    ("(print,)", is_ok()),
    ("(print, lambda x: None,)", is_ok()),
    ("(print, lambda x: None,)", is_ok()),
    ("(None,)", raises(TypeError, match="handler must be a callable")),
    ("(object(),)", raises(TypeError, match="handler must be a callable")),
    ("((print, ()),)", raises(TypeError, match=r"Cannot use an empty \w+ as failure specification")),
    ("((print, object()),)", raises(TypeError, match="Unsupported filter type")),
    ("((print, Not('*')),)", raises(ValueError, match="Cannot filter out all failures")),
    ("((print, Not(Exception)),)", raises(ValueError, match="Cannot filter out all failures")),
    ("((print, Not(ValueError, '*')),)", raises(ValueError, match="Cannot filter out all failures")),
    ("(((), (ValueError,)),)", raises(TypeError, match="Cannot define an empty tuple as failure handler")),
    ("(((print,), (ValueError,)),)", is_ok()),
])
def test_handler_arg_validation(args, expectation):
    with expectation:
        Handler(*eval(args))


def test_default_handler_function():
    assert getattr(Handler(), '_Handler__handler') is print_failure


VE = ValueError("Test")
TE = TypeError("Test")
KE = KeyError("Test")
IE = IndexError("Test")
FAILURES = [
    Failure("source1.action1.sub", VE, {}),
    Failure("source1.action1", TE, {}),
    Failure("source1.action2.sub", VE, {}),
    Failure("source2.action2", TE, {}),
    Failure("source2.action1.sub", KE, {}),
    Failure("source2.action2.sub", IE, {}),
]


@mark.parametrize("flt, fls", [
    param(('*',), (0, 1, 2, 3, 4, 5,), id="wild-card-label"),
    param((Exception,), (0, 1, 2, 3, 4, 5,), id="all-exception-types"),
    param(([ValueError, TypeError],), (0, 1, 2, 3,), id="value-or-type-error"),
    param((Not(ValueError, TypeError),), (4, 5,), id="not-value-or-type-error"),
    param(((Not(ValueError), Not(TypeError)),), (4, 5,), id="not-value-or-type-error-separated"),
    param((LookupError,), (4, 5,), id="sub-class-errors"),
    param(((ValueError, TypeError),), (), id="value-and-type-error"),
    param(('source1.action1.sub',), (0,), id="specific-label"),
    param(('source1.*',), (0, 1, 2,), id="failure-starting-with-source1"),
    param((('*.sub', ValueError),), (0, 2,), id="value-error-endswith-sub"),
    param((Not(('*.sub', ValueError)),), (1, 3, 4, 5), id="not-value-error-endswith-sub"),
])
def test_filter_combination(flt, fls):
    ls = []
    handler = Handler((ls.append, flt))
    for failure in FAILURES:
        handler(failure)
    assert ls == [FAILURES[fl] for fl in fls]
