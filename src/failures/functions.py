"""
functions.py module implements functions decorators and utilities to reduce and automate common tasks needed
by this library like labeling the top level scope of functions.
"""
from __future__ import annotations
import types
import inspect
import functools
from typing import Callable, Any, Optional, Union, Dict, Tuple, overload, cast, Awaitable

from typing_extensions import get_origin, get_args

from .core import Reporter, P, T, _invalid

REPORTER_ARG_NAME = 'reporter'
NOTSET = object()

_union_types: list = [Union]
try:
    _union_types.append(types.UnionType)
except AttributeError:
    pass


def _is_param_reporter(name: str, annotation: Any, default: Any) -> bool:
    _type_hinted_reporter = (annotation is Reporter or
                             (get_origin(annotation) in _union_types and
                              Reporter in get_args(annotation)))
    _name_hinted_reporter = name == REPORTER_ARG_NAME and annotation is NOTSET
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
            default = spec.defaults[idx - len(spec.args)]  # type: ignore
        except (IndexError, TypeError):
            default = NOTSET
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET), default):
            continue

        def _get(_args: tuple, _kwargs: Dict[str, Any], /) -> Optional[Reporter]:
            try:
                return _args[idx]
            except IndexError:
                if default is not NOTSET:
                    return default
                raise _invalid(TypeError, f"{name}() is missing the reporter as required positional argument") from None

        def _set(_args: tuple, _kwargs: Dict[str, Any], _reporter: Reporter, /) -> Tuple[tuple, Dict[str, Any]]:
            args = list(_args)
            try:
                args[idx] = _reporter
            except IndexError:
                args.append(_reporter)
            return tuple(args), _kwargs

        return _get, _set

    # Check if keyword arguments contain the reporter
    for _arg in spec.kwonlyargs:
        try:
            default = spec.kwonlydefaults[_arg]  # type: ignore  # Brutal access
        except (KeyError, TypeError):
            default = NOTSET
        if not _is_param_reporter(_arg, spec.annotations.get(_arg, NOTSET), default):
            continue

        def _get(_args: tuple, _kwargs: Dict[str, Any], /) -> Optional[Reporter]:
            try:
                return _kwargs[_arg]
            except KeyError:
                if default is not NOTSET:
                    return default
                raise _invalid(TypeError, f"{name}() is missing the reporter as required keyword argument") from None

        def _set(_args: tuple, _kwargs: Dict[str, Any], _reporter: Reporter, /) -> Tuple[tuple, Dict[str, Any]]:
            _kwargs[_arg] = _reporter
            return _args, _kwargs

        return _get, _set

    # Return default 'get' and 'set' functions
    def _get(_args: tuple, _kwargs: Dict[str, Any], /) -> Optional[Reporter]:  # type: ignore[no-redef]
        return None

    def _set(  # type: ignore[no-redef]
            _args: tuple,
            _kwargs: Dict[str, Any],
            _reporter: Reporter, /
    ) -> Tuple[tuple, Dict[str, Any]]:
        return _args, _kwargs

    return _get, _set


def is_async(func: Callable, /) -> bool:
    while isinstance(func, functools.partial):
        func = func.func
    return inspect.iscoroutinefunction(func) or (
        hasattr(func, '__call__') and
        inspect.iscoroutinefunction(func.__call__)
    )


def get_func_name(func: Callable, /) -> str:
    while isinstance(func, functools.partial):
        func = func.func
    return func.__name__


@overload
def scoped(func: Callable[P, T], /) -> Callable[P, T]: ...
@overload
def scoped(name: str = ..., /) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


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
    def decorator(func_: Callable[P, T], /, name: str = None) -> Callable[P, T]:
        _get, _set = _get_set_reporter_from_signature(func_)
        name_ = name or get_func_name(func_)

        def get_reporter(args, kwargs) -> Reporter:
            reporter: Optional[Callable[[str], Reporter]] = _get(args, kwargs)
            if reporter is None:
                reporter = Reporter
            elif not isinstance(reporter, Reporter):
                raise _invalid(TypeError, f"The reporter got wrong type {type(reporter)!r}")
            return reporter(name_)

        if is_async(func_):
            @functools.wraps(func_)
            async def wrap(*args: P.args, **kwargs: P.kwargs) -> T:
                reporter = get_reporter(args, kwargs)
                _args, _kwargs = _set(args, kwargs, reporter)
                with reporter:
                    return await cast(Callable[P, Awaitable[T]], func_)(*_args, **_kwargs)
        else:
            @functools.wraps(func_)
            def wrap(*args: P.args, **kwargs: P.kwargs) -> T:
                reporter = get_reporter(args, kwargs)
                _args, _kwargs = _set(args, kwargs, reporter)
                with reporter:
                    return func_(*_args, **_kwargs)
        setattr(wrap, '__signature__', inspect.signature(func_))
        return cast(Callable[P, T], wrap)
    if arg is None:  # In case it was used with emtpy parenthesis @scope()
        return decorator
    elif callable(arg):  # In case it was used without parenthesis @scope
        return decorator(arg)
    elif isinstance(arg, str):  # In case it was called with a name @scope("name")
        return lambda func: decorator(func, arg)
    raise _invalid(TypeError, "@scoped decorator expects a callable as first argument")
