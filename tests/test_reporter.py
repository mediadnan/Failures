import asyncio
from typing import Union, Optional, Tuple, List

from pytest import param, raises, mark

from failures import Reporter, Failure, FailureException
from failures.core import _invalid, _ReporterChild


# Note:
#   Some test functions use explicit if not (...): raise AssertionError instead of assert statements,
#   the reason is to make those tests run in both normal and optimized modes, as running python3 -O
#   disables assert statements.


@mark.parametrize("name", [
    "root", "root.sub", "root.sub_scope",
    "root.sub.sub.sub", "root.scope1",
    "scope2", "scope.iteration[5].func",
    "scope.func(1)", "iter[255]", "r"
])
def test_reporter_valid_names(name: str):
    # Valid for first reporter
    reporter = Reporter(name)
    if reporter.name != name:
        raise AssertionError(f"Unexpected name {__debug__=}")
    if reporter.label != name:
        raise AssertionError(f"Unexpected label {__debug__=}")
    # Valid for sub reporter
    reporter = reporter(name)
    if reporter.name != name:
        raise AssertionError(f"Unexpected name {__debug__=}")
    if reporter.label != f"{name}.{name}":
        raise AssertionError(f"Unexpected label {__debug__=}")


@mark.skipif(__debug__ is False, reason="No validation is done with optimized mode")
@mark.parametrize("name, catch_failure", [
    param(object(), raises(TypeError), id="wrong_name_type"),
    param(b'name.sub', raises(TypeError), id="wrong_type_name_bytes"),
    param('', raises(ValueError), id="empty_name"),
    param('name..sub', raises(ValueError), id="double_dot"),
    param('.name', raises(ValueError), id="leading_dot"),
    param('name.', raises(ValueError), id="trailing_dot"),
])
def test_reporter_invalid_names(name: str, catch_failure):
    # Invalid for first reporter
    with catch_failure:
        Reporter(name)
    # Invalid for sub reporter
    with catch_failure:
        Reporter("rep")(name)


@mark.skipif(__debug__ is False, reason="No validation is done with optimized mode")
def test_direct_reporter_child_creation():
    with raises(TypeError):
        _ReporterChild("rep", None)  # type: ignore


@mark.parametrize("details", [{}, {'input': 27, 'desc': "cubic root evaluation"}], ids=str)
def test_reporter_creation(details):
    # Testing the first reporter
    reporter = Reporter("main", **details)
    assert reporter.name == "main"
    assert reporter.label == "main"
    assert reporter.details == details
    assert reporter.failures == []
    assert reporter.parent is None
    assert reporter.root is reporter
    assert repr(reporter) == "Reporter('main')"

    # Testing the next reporter
    sub_reporter = reporter("sub", env="prod", input=125)
    assert sub_reporter.name == "sub"
    assert sub_reporter.label == "main.sub"
    assert sub_reporter.details == {**details, 'env': "prod", 'input': 125}
    assert sub_reporter.failures is reporter.failures
    assert sub_reporter.parent is reporter
    assert sub_reporter.root is reporter
    assert repr(sub_reporter) == "Reporter('main.sub')"

    # Testing a further reporter
    sub_sub_reporter = sub_reporter("leaf")
    assert sub_sub_reporter.name == "leaf"
    assert sub_sub_reporter.label == "main.sub.leaf"
    assert sub_sub_reporter.details == sub_reporter.details
    assert sub_sub_reporter.failures is reporter.failures
    assert sub_sub_reporter.parent is sub_reporter
    assert sub_sub_reporter.root is reporter
    assert repr(sub_sub_reporter) == "Reporter('main.sub.leaf')"


def test_reporter_report():
    root = Reporter('root')
    sub = root('sub', context="something")
    last = sub('last')
    ve = ValueError("test")
    te = TypeError("test")
    ie = IndexError("test")
    root.report(ve, input="-5")
    sub.report(te, input=None, context="another")
    last.report(ie, input=11)

    assert root.failures == [
        Failure("root", ve, {'input': '-5'}),
        Failure("root.sub", te, {'input': None, 'context': "another"}),
        Failure("root.sub.last", ie, {'input': 11, 'context': "something"}),
    ]


def test_reporter_context_manager_return():
    """Test the returned value of the reporter as a context manager"""
    reporter = Reporter("ctx")
    with reporter as rep:
        pass
    assert rep is reporter


def test_report_context_manager_bound_labeled_failure(error):
    try:
        with Reporter("rep-ctx", data=None) as reporter:
            with reporter("sub", input="abc"):
                raise error
    except FailureException as fe:
        assert fe.failure == Failure(
            "rep-ctx.sub",
            error,
            {'data': None, 'input': "abc"}
        )


def test_report_context_manager_unbound_labeled_failure(error):
    try:
        with Reporter("rep-ctx", data=None):
            with Reporter("sub", input="abc"):
                raise error
    except FailureException as fe:
        assert fe.failure == Failure(
            "rep-ctx.sub",
            error,
            {'data': None, 'input': "abc"}
        )


def test_report_context_manager_labeled_failure(error):
    try:
        with Reporter("rep-ctx", data=None):
            raise error
    except FailureException as fe:
        assert fe.failure == Failure(
            "rep-ctx",
            error,
            {'data': None}
        )


@mark.parametrize('err', [
    BaseException("test"),
    KeyboardInterrupt("test"),
    GeneratorExit("test"),
    SystemExit("test"),
    _invalid(TypeError, "test"),
    _invalid(Exception, "test"),
    _invalid(ValueError, "test"),
], ids=repr)
def test_reporter_context_avoids_high_and_validation_exception(err):
    try:
        with Reporter("avoid"):
            raise err
    except BaseException as exc:
        assert not isinstance(exc, FailureException)


def test_hybrid_bound_unbound_failure(error):
    reporter = Reporter("root")("sub", a=5)("sub")("last", b=7)
    try:
        with Reporter("top") as top:
            with reporter:
                with Reporter("deep", c=11):
                    raise error
    except FailureException as fe:
        assert fe.reporter is top
        assert fe.failure == Failure(
            "top.root.sub.sub.last.deep",
            error,
            dict(a=5, b=7, c=11)
        )


INVALID_CONTAINER_ERROR = TypeError("Invalid container type")


def populate(*args, cont: Union[list, dict], **kwargs) -> None:
    if isinstance(cont, list):
        return cont.extend(args)
    elif isinstance(cont, dict):
        return cont.update(kwargs)
    raise INVALID_CONTAINER_ERROR


async def populate_async(*args, cont: Union[list, dict], **kwargs) -> None:
    await asyncio.sleep(0.001)
    return populate(*args, cont=cont, **kwargs)


@mark.parametrize("meth, expected, raised, reported", [
    ("safe", ([1, 2], {'a': 'a', 'b': 'b'}), None, [Failure("rep", INVALID_CONTAINER_ERROR, {'desc': "details..."})]),
    ("optional", ([1, 2], {'a': 'a', 'b': 'b'}), None, []),
    ("required", ([1, 2], {}), Failure("rep", INVALID_CONTAINER_ERROR, {'desc': "details..."}), []),
])
def test_reporter_exec_ctx(meth: str, expected: Tuple[list, dict], raised: Optional[Failure], reported: List[Failure]):
    data = (
        [],  # inserted before failure
        {},  # inserted after failure
    )
    reporter = Reporter("rep", desc="details...")
    method = getattr(reporter, meth)
    _raised = None
    try:
        method(populate, 1, 2, cont=data[0], a='a', b='b')
        method(populate, 1, 2, cont=None, a='a', b='b')
        method(populate, 1, 2, cont=data[1], a='a', b='b')
    except FailureException as fe:
        assert raised == fe.failure
    else:
        assert raised is None
    assert data == expected
    assert reporter.failures == reported


@mark.parametrize("meth, expected, raised, reported", [
    ("safe_async", ([1, 2], {'a': 'a', 'b': 'b'}), None, [Failure("rep", INVALID_CONTAINER_ERROR, {'desc': "details"})]),
    ("optional_async", ([1, 2], {'a': 'a', 'b': 'b'}), None, []),
    ("required_async", ([1, 2], {}), Failure("rep", INVALID_CONTAINER_ERROR, {'desc': "details"}), []),
])
@mark.asyncio
async def test_reporter_async_exec_ctx(meth: str, expected: Tuple[list, dict], raised: Optional[Failure], reported: List[Failure]):
    data = (
        [],  # inserted before failure
        {},  # inserted after failure
    )
    reporter = Reporter("rep", desc="details")
    method = getattr(reporter, meth)
    _raised = None
    try:
        await method(populate_async, 1, 2, cont=data[0], a='a', b='b')
        await method(populate_async, 1, 2, cont=None, a='a', b='b')
        await method(populate_async, 1, 2, cont=data[1], a='a', b='b')
    except FailureException as fe:
        assert raised == fe.failure
    else:
        assert raised is None
    assert data == expected
    assert reporter.failures == reported
