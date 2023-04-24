import functools
import types
import inspect
from typing import TypeVar, Callable, Any, Optional, Union, Dict, Tuple

from typing_extensions import ParamSpec, get_origin, get_args

from .core import Reporter, FailureHandler, FailureException

T = TypeVar('T')
P = ParamSpec('P')
FunctionVar = TypeVar('FunctionVar', bound=Callable)

REPORTER_ARG_NAME = 'reporter'
NOTSET = object()

_union_types = [Union]
try:
    _union_types.append(types.UnionType)
except AttributeError:
    pass


def _is_param_reporter(name: str, annotation: Any) -> bool:
    _reporter_hint = (annotation is Reporter or
                      (get_origin(annotation) in _union_types and
                       Reporter in get_args(annotation)))
    _no_annotation = annotation is NOTSET
    return _reporter_hint or (name == 'reporter' and _no_annotation)


def detect_signature_reporter(func: FunctionVar, /) -> Tuple[
    FunctionVar,
    Callable[[tuple, Dict[str, Any]], Optional[Reporter]],
    Callable[[tuple, Dict[str, Any], Reporter], Tuple[tuple, Dict[str, Any]]],
]:
    spec = inspect.getfullargspec(func)
    for idx, _arg in enumerate(spec.args):
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET)):
            continue

        def _get(args: tuple, _kwargs: Dict[str, Any]) -> Optional[Reporter]:
            return args[idx]

        def _set(args: tuple, kwargs: Dict[str, Any], reporter: Reporter) -> Tuple[tuple, Dict[str, Any]]:
            _args = list(args)
            _args[idx] = reporter
            return tuple(_args), kwargs
        return func, _get, _set
    for _arg in spec.kwonlyargs:
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET)):
            continue

        def _get(_args: tuple, kwargs: Dict[str, Any]) -> Optional[Reporter]:
            return kwargs[_arg]

        def _set(args: tuple, kwargs: Dict[str, Any], reporter: Reporter) -> Tuple[tuple, Dict[str, Any]]:
            kwargs[_arg] = reporter
            return args, kwargs
        return func, _get, _set
    return func, lambda a, k: None, lambda a, k, r: (a, k)


def is_async(func: FunctionVar, /) -> bool:
    while isinstance(func, functools.partial):
        func = func.func
    return inspect.iscoroutinefunction(func) or (
        hasattr(func, '__call__') and
        inspect.iscoroutinefunction(func.__call__)
    )


def get_func_name(func: FunctionVar, /) -> str:
    while isinstance(func, functools.partial):
        func = func.func
    return func.__name__


def _decorator(
        func_: Optional[FunctionVar], name_: Optional[str], handler: Callable[[Reporter, Exception], None]
) -> Union[FunctionVar, Callable[[FunctionVar], FunctionVar]]:
    def decorator(func: FunctionVar, /) -> FunctionVar:
        if not callable(func):
            raise TypeError("decorated function must be callable")
        func, _get, _set = detect_signature_reporter(func)
        name = name_ or get_func_name(func)
        if is_async(func):
            async def wrap(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
                reporter = (_get(args, kwargs) or Reporter)(name)
                args, kwargs = _set(args, kwargs, reporter)
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    handler(reporter, error)
        else:
            def wrap(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
                reporter = (_get(args, kwargs) or Reporter)(name)
                args, kwargs = _set(args, kwargs, reporter)
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    handler(reporter, error)
        wrap.__signature__ = inspect.signature(func)
        return functools.update_wrapper(wrap, func)
    return decorator if func_ is None else decorator(func_)


def _ignore_failure(_reporter: Reporter, _error: Exception) -> None:
    return


def _report_failure(reporter: Reporter, error: Exception) -> None:
    reporter.report(error)


def _propagate_failure(reporter: Reporter, error: Exception) -> None:
    raise FailureException(reporter.failure(error), reporter)


def optional(func: Callable[P, T] = None, /, *, name: str = None):
    return _decorator(func, name, _ignore_failure)


def safe(func: Callable[P, T] = None, /, *, name: str = None):
    return _decorator(func, name, _report_failure)


def labeled(func: Callable[P, T] = None, /, *, name: str = None):
    return _decorator(func, name, _propagate_failure)


def get_optional(reporter: Reporter, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
    pass


def get(reporter: Reporter, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
    pass


def get_required(reporter: Reporter, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
    pass
