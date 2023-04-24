import functools
import types
import inspect
from typing import Callable, Any, Optional, Union, Dict, Tuple, overload

from typing_extensions import get_origin, get_args

from .core import Reporter, P, T, FunctionVar

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


@overload
def scoped(func: FunctionVar, /) -> FunctionVar: ...
@overload
def scoped(name: str = ..., /) -> Callable[[FunctionVar], FunctionVar]: ...


def scoped(arg: Union[FunctionVar, str, None] = None, /) -> Union[FunctionVar, Callable[[FunctionVar], FunctionVar]]:
    """
    Decorates functions to intercept any inner failures and add
    the function name to its label, and also add the function's
    name to any reporter passed as argument to that function.

    This decorator can be either parametrized or not.

    >>> @scoped
    ... def function(*args, **kwars):
    ...     pass

    or

    >>> @scoped('my_function')
    ... def function(*args, **kwars):
    ...     pass
    """
    def decorator(func_: FunctionVar, /, name: str = None) -> FunctionVar:
        if not callable(func_):
            raise TypeError("@scoped decorator expects a function")
        func_, _get, _set = detect_signature_reporter(func_)
        name_ = name or get_func_name(func_)
        if is_async(func_):
            async def wrap(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
                reporter = (_get(args, kwargs) or Reporter)(name_)
                args, kwargs = _set(args, kwargs, reporter)
                with reporter:
                    return await func_(*args, **kwargs)
        else:
            def wrap(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
                reporter = (_get(args, kwargs) or Reporter)(name_)
                args, kwargs = _set(args, kwargs, reporter)
                with reporter:
                    return func_(*args, **kwargs)
        wrap.__signature__ = inspect.signature(func_)
        return functools.update_wrapper(wrap, func_)
    if arg is None:
        return decorator
    elif callable(arg):
        return decorator(arg)
    elif isinstance(arg, str):
        return lambda func: decorator(func, arg)
    raise TypeError("@scoped decorator expects a callable as first argument")
