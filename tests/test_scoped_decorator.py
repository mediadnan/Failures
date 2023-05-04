from functools import partial
from typing import Optional

from pytest import mark, fixture, raises
from failures import scoped, FailureException, Reporter, Failure

ERROR = Exception("test error")


@fixture
def reporter():
    return Reporter('root')


def func_without_params(): raise ERROR
def func_with_params(_mandatory: int, *_, _param: str, **__): raise ERROR
def func_with_opt_params(_optional: int = None, *_, _param: str = None, **__): raise ERROR


partially_initialized_function = partial(func_with_params, 5, _param='five')


def func_with_opt_arg_reporter(_arg=None, reporter=None):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_kwarg_reporter(*_args, reporter=None):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_kwarg_reporter_ann(*_args, rep: Reporter = None):
    (rep or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_kwarg_reporter_ann_name(*_args, reporter: Reporter = None):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_kwarg_reporter_ann_optional(*_args, reporter: Optional[Reporter] = None):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_req_kwarg_reporter_ann_excluded(*_args, reporter: list):
    raise ERROR


def func_with_opt_kwarg_reporter_def_excluded(*_args, reporter: Reporter = ()):
    raise ERROR


def func_with_req_arg_reporter(_arg, reporter, *_args):
    reporter("sub").report(ERROR)
    raise ERROR


def func_with_req_kwarg_reporter(*_args, reporter):
    reporter("sub").report(ERROR)
    raise ERROR


def func_with_req_arg_reporter_ann(rep: Reporter, *_args):
    (rep or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_arg_reporter_ann_name(reporter: Reporter = None, *_args):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_arg_reporter_ann_optional(reporter: Optional[Reporter] = None, *_args):
    (reporter or Reporter)("sub").report(ERROR)
    raise ERROR


def func_with_opt_arg_reporter_ann_excluded(reporter: list, *_args):
    raise ERROR


def func_with_opt_arg_reporter_def_excluded(reporter: Reporter = (), *_args):
    raise ERROR


@mark.parametrize("decorator, name", [
    ("scoped", None),
    ("scoped()", None),
    ("scoped('my_func')", "my_func"),
    # ("scoped('decorated-func[11]')", "decorated-func[11]"),
])
@mark.parametrize("func, func_name, args, kwargs, bound", [
    (func_without_params, "func_without_params", "(3,)", "{'_param': 'three'}", False),
    (func_with_params, "func_with_params", "()", "{}", False),
    (partially_initialized_function, "func_with_params", "()", "{}", False),
    (func_with_opt_params, "func_with_opt_params", "()", "{}", False),
    (func_with_opt_arg_reporter, "func_with_opt_arg_reporter", "()", "{}", False),
    (func_with_opt_arg_reporter, "func_with_opt_arg_reporter", "(None, reporter,)", "{}", True),
    (func_with_req_arg_reporter, "func_with_req_arg_reporter", "(None, reporter,)", "{}", True),
    (func_with_opt_kwarg_reporter, "func_with_opt_kwarg_reporter", "()", "{}", False),
    (func_with_opt_kwarg_reporter, "func_with_opt_kwarg_reporter", "()", "{'reporter': reporter}", True),
    (func_with_req_kwarg_reporter, "func_with_req_kwarg_reporter", "()", "{'reporter': reporter}", True),
    (func_with_opt_kwarg_reporter_ann, "func_with_opt_kwarg_reporter_ann", "()", "{'rep': reporter}", True),
    (func_with_opt_kwarg_reporter_ann, "func_with_opt_kwarg_reporter_ann", "()", "{}", False),
    (func_with_opt_kwarg_reporter_ann_name, "func_with_opt_kwarg_reporter_ann_name", "()", "{'reporter': reporter}", True),
    (func_with_opt_kwarg_reporter_ann_optional, "func_with_opt_kwarg_reporter_ann_optional", "()", "{}", False),
    (func_with_opt_kwarg_reporter_ann_optional, "func_with_opt_kwarg_reporter_ann_optional", "()", "{'reporter': reporter}", True),
    (func_with_req_kwarg_reporter_ann_excluded, "func_with_req_kwarg_reporter_ann_excluded", "()", "{'reporter': reporter}", False),
    (func_with_opt_kwarg_reporter_def_excluded, "func_with_opt_kwarg_reporter_def_excluded", "()", "{'reporter': reporter}", False),
    (func_with_req_arg_reporter_ann, "func_with_req_arg_reporter_ann", "(reporter,)", "{}", True),
    (func_with_opt_arg_reporter_ann_name, "func_with_opt_arg_reporter_ann_name", "()", "{}", False),
    (func_with_opt_arg_reporter_ann_name, "func_with_opt_arg_reporter_ann_name", "(reporter,)", "{}", True),
    (func_with_opt_arg_reporter_ann_optional, "func_with_opt_arg_reporter_ann_optional", "()", "{}", False),
    (func_with_opt_arg_reporter_ann_optional, "func_with_opt_arg_reporter_ann_optional", "(reporter,)", "{}", True),
    (func_with_opt_arg_reporter_ann_excluded, "func_with_opt_arg_reporter_ann_excluded", "(reporter,)", "{}", False),
    (func_with_opt_arg_reporter_def_excluded, "func_with_opt_arg_reporter_def_excluded", "(reporter,)", "{}", False),
])
def test_decorator_no_params_func_no_rep(reporter, decorator, name, func, func_name, args, kwargs, bound):
    func = eval(decorator)(func)
    if name is None:
        name = func_name
    if bound:
        name = f'root.{name}'
    try:
        func(*eval(args), **eval(kwargs))
    except FailureException as fe:
        assert fe.failure.source == name
    assert (reporter.failures == [Failure(f"{name}.sub", ERROR, {})]) is bound


@mark.parametrize("code", [
    "scoped(object())",
    "scoped(None)(None)",
    "scoped()(None)",
])
def test_invalid_type_decoration(code: str):
    with raises(TypeError):
        eval(code)
