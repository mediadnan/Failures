import types
import inspect
import functools
from typing import Callable, Any, Optional, Union, Dict, Tuple, overload

from typing_extensions import get_origin, get_args

from .core import Reporter, P, T, FunctionVar, _invalid

REPORTER_ARG_NAME = 'reporter'
NOTSET = object()

_union_types = [Union]
try:
    _union_types.append(types.UnionType)
except AttributeError:
    pass


def _is_param_reporter(name: str, annotation: Any, default: Any) -> bool:
    _type_hinted_reporter = (annotation is Reporter or
                             (get_origin(annotation) in _union_types and
                              Reporter in get_args(annotation)))
    _name_hinted_reporter = name == 'reporter' and annotation is NOTSET
    _right_default = default is NOTSET or default is None or isinstance(default, Reporter)
    return (_type_hinted_reporter or _name_hinted_reporter) and _right_default


def _get_set_reporter_from_signature(func: Callable, /) -> Tuple[
    Callable[[tuple, Dict[str, Any]], Optional[Reporter]],
    Callable[[tuple, Dict[str, Any], Reporter], Tuple[tuple, Dict[str, Any]]],
]:
    spec = inspect.getfullargspec(func)
    name = get_func_name(func)

    # Check if positional arguments contain the reporter
    for idx, _arg in enumerate(spec.args):
        try:
            default = spec.defaults[idx - len(spec.args)]
        except (IndexError, TypeError):
            default = NOTSET
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET), default):
            continue

        def _get(args: tuple, _kwargs: Dict[str, Any]) -> Optional[Reporter]:
            try:
                return args[idx]
            except IndexError:
                if default is not NOTSET:
                    return default
                raise _invalid(TypeError, f"{name}() is missing the reporter as required positional argument") from None

        def _set(args: tuple, kwargs: Dict[str, Any], reporter: Reporter) -> Tuple[tuple, Dict[str, Any]]:
            _args = list(args)
            try:
                _args[idx] = reporter
            except IndexError:
                _args.append(reporter)
            return tuple(_args), kwargs

        return _get, _set

    # Check if keyword arguments contain the reporter
    for _arg in spec.kwonlyargs:
        try:
            default = spec.kwonlydefaults[_arg]
        except (KeyError, TypeError):
            default = NOTSET
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET), default):
            continue
        if default is NOTSET:
            default = None

        def _get(_args: tuple, kwargs: Dict[str, Any]) -> Optional[Reporter]:
            try:
                return kwargs[_arg]
            except KeyError:
                if default is not NOTSET:
                    return default
                raise _invalid(TypeError, f"{name}() is missing the reporter as required keyword argument") from None

        def _set(args: tuple, kwargs: Dict[str, Any], reporter: Reporter) -> Tuple[tuple, Dict[str, Any]]:
            kwargs[_arg] = reporter
            return args, kwargs

        return _get, _set

    # Return default 'get' and 'set' functions
    return lambda _a, _k: None, lambda a, k, _: (a, k)


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


def scoped(arg=None, /):
    """
    Decorates functions to intercept any inner failures and add
    the function name to its label, and also add the function's
    name to any reporter passed as argument to that function.

    This decorator can be either parametrized or not.

    >>> @scoped
    ... def function(*args, **kwargs):
    ...     pass

    or

    >>> @scoped('my_function')
    ... def function(*args, **kwargs):
    ...     pass
    """
    def decorator(func_: FunctionVar, /, name: str = None) -> FunctionVar:
        _get, _set = _get_set_reporter_from_signature(func_)
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
    if arg is None:  # In case it was used with emtpy parenthesis @scope()
        return decorator
    elif callable(arg):  # In case it was used without parenthesis @scope
        return decorator(arg)
    elif isinstance(arg, str):  # In case it was called with a name @scope("name")
        return lambda func: decorator(func, arg)
    raise TypeError("@scoped decorator expects a callable as first argument")
