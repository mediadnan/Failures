from typing import Type

import pytest
from failures import Reporter, Failure, FailureException
from failures.core import _invalid


@pytest.mark.parametrize("name", [
    "root", "root.sub", "root.sub_scope",
    "root.sub.sub.sub", "root.scope1",
    "scope2", "scope.iteration[5].func",
    "scope.func(1)", "iter[255]", "r"
])
def test_reporter_valid_names(name: str):
    # Valid for first reporter
    reporter = Reporter(name)
    assert reporter.name == name
    assert reporter.label == name
    # Valid for sub reporter
    reporter = reporter(name)
    assert reporter.name == name
    assert reporter.label == f"{name}.{name}"


@pytest.mark.parametrize("name, error, message", [
    pytest.param(object(), TypeError, "label must be a string", id="wrong_type_name"),
    pytest.param(b'name.sub', TypeError, "label must be a string", id="wrong_type_name_bytes"),
    pytest.param('', ValueError, "invalid label: ''", id="empty_name"),
    pytest.param('name..sub', ValueError, "invalid label: 'name..sub'", id="double_dot"),
    pytest.param('.name', ValueError, "invalid label", id="leading_dot"),
    pytest.param('name.', ValueError, "invalid label", id="trailing_dot"),
])
def test_reporter_invalid_names(name: str, error: Type[Exception], message: str):
    # Invalid for first reporter
    with pytest.raises(error, match=message):
        Reporter(name)
    # Invalid for sub reporter
    with pytest.raises(error, match=message):
        Reporter("rep")(name)


@pytest.mark.parametrize("details", [{}, {'input': 27, 'desc': "cubic root evaluation"}], ids=str)
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

    # Testing further reporter
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


@pytest.mark.parametrize('err', [
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
