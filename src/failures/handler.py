"""
handler.py module implements tools for handling and processing failures gathered or raised
by reporters, and tools to filter between failures either by label or by error type and combine
multiple failure handling functions.
"""
import re
import abc
from typing import Pattern, List, Literal, Callable, Type, Tuple, Union, cast
from datetime import datetime

try:
    import colorama
except ImportError:
    _template = "[FAILURE] {source} :: {err_type}({error}) {time}"
else:
    colorama.just_fix_windows_console()
    _template = (
        f"{colorama.Style.BRIGHT + colorama.Fore.LIGHTRED_EX}[FAILURE] "
        f"{colorama.Style.BRIGHT + colorama.Fore.WHITE}{{source}}{colorama.Style.RESET_ALL} :: "
        f"{colorama.Style.BRIGHT + colorama.Fore.LIGHTRED_EX}{{err_type}}({colorama.Style.RESET_ALL}"
        f"{colorama.Fore.LIGHTWHITE_EX}{{error}}{colorama.Fore.RESET}"
        f"{colorama.Style.BRIGHT + colorama.Fore.LIGHTRED_EX}){colorama.Style.RESET_ALL} "
        f"{colorama.Style.DIM + colorama.Fore.CYAN}{{time}}{colorama.Fore.RESET}{colorama.Style.RESET_ALL}"
    )
from typing_extensions import TypeAlias, Self

from .core import Failure, FailureException, Reporter, _invalid

# Type aliases
FailureFilter: TypeAlias = Callable[['Failure'], bool]
FailureHandler: TypeAlias = Callable[['Failure'], None]
HandlerOrHandlers = Union[FailureHandler, Tuple[FailureHandler, ...]]
ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]
SupportedFilters: TypeAlias = Union[str, ExceptionTypes, 'FailureMatch']
Filters: TypeAlias = Union[SupportedFilters, Tuple['Filters', ...], List['Filters']]


def print_failure(failure: Failure, /) -> None:
    """Logs the failure to the standard output"""
    error = failure.error
    source = failure.source
    err_type = type(error).__name__
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(_template.format(source=source, err_type=err_type, error=error, time=time))


class FailureMatch(abc.ABC):
    @abc.abstractmethod
    def __call__(self, failure: Failure, /) -> bool:
        """Checks if the failure matches the specification"""


class FailureLabelMatch(FailureMatch):
    __slots__ = ('label',)
    label: str

    def __init__(self, label: str, /):
        self.label = label

    def __call__(self, failure: Failure, /) -> bool:
        """Checks if the failure's source matches the specification"""
        return failure.source == self.label


class FailureLabelPatternMatch(FailureMatch):
    __slots__ = ('pattern',)
    pattern: Pattern[str]

    def __init__(self, pattern: str, /):
        self.pattern = re.compile(re.escape(pattern).replace(r'\*', '.*'), re.DOTALL)

    def __call__(self, failure: Failure, /) -> bool:
        """Checks if the failure's source matches the specification"""
        return bool(self.pattern.match(failure.source))


class FailureExceptionMatch(FailureMatch):
    __slots__ = ('exc_type',)
    exc_type: ExceptionTypes

    def __init__(self, exc_type: ExceptionTypes, /) -> None:
        self.exc_type = exc_type

    def __call__(self, failure: Failure, /) -> bool:
        """Checks if the failure's error matches the specification"""
        err = failure.error
        exp = self.exc_type
        return isinstance(err, exp) or (isinstance(err, type) and issubclass(err, exp))


def _match_all(_: Failure, /) -> Literal[True]:
    """Matches all the failures"""
    return True


def _validate_handler(obj: FailureHandler) -> FailureHandler:
    """Validates the failure handler function"""
    if not callable(obj):
        raise TypeError("the handler must be a callable with signature: (Failure) -> None")
    return obj


def filters(spec: Filters, /) ->FailureFilter:
    """
    Creates a failure filter function that takes a failure object
    and returns True or False whether it matches the specification
    or not.

    :param spec: Either a single filter specifier or a combination list and/or tuple of filters.
    :returns: A Filter function based on that specifier(s).
    """
    if isinstance(spec, FailureMatch) or spec is _match_all:
        # for prepared filters
        return cast(Union[FailureMatch, FailureFilter], spec)
    if isinstance(spec, (tuple, list)):
        if not spec:
            raise _invalid(TypeError, f"Cannot use an empty {type(spec).__name__} as failure specification")
        _filters = list(map(filters, spec))
        if len(_filters) == 1:
            return _filters[0]
        if isinstance(spec, list):
            if _match_all in _filters:
                return _match_all
            comb = any
        else:
            comb = all

        def check(failure: Failure) -> bool:
            return comb((_filter(failure) for _filter in _filters))
        return check
    if spec == '*' or spec is Exception:
        return _match_all  # optimising match
    if isinstance(spec, str):
        if '*' in spec:
            return FailureLabelPatternMatch(spec)
        return FailureLabelMatch(spec)
    if isinstance(spec, type) and issubclass(spec, Exception):
        return FailureExceptionMatch(spec)
    raise TypeError(f"Unsupported filter type {type(spec)!r}")


class Not(FailureMatch):
    """
    Matches the opposite of the specified filters,
    like ``Not(ValueError)`` matches every failure
    but ``ValueError``.

    If we want to avoid multiple failures, we can pass
    multiple filters, like ``Not(TypeError, ValueError)``
    this is like writing ``not isinstance(error, (TypeError, ValueError))``.
    """
    __slots__ = '_filter',

    def __init__(self, *spec: Filters) -> None:
        self._filter: FailureFilter = filters(
            spec[0]   # In case the user passes a prepared filter
            if len(spec) == 1 else
            list(spec)
        )
        if self._filter is _match_all:
            raise ValueError("Cannot filter out all failures")

    def __call__(self, failure: Failure, /) -> bool:
        return not self._filter(failure)


def filtered(handler: FailureHandler, condition: FailureFilter) -> FailureHandler:
    """
    Turns the failure handler function into a conditional handler
    only applied to the failure if the condition is met.

    :param handler: The function that handles the failure ``(failure) -> None``,
    :param condition: The function that checks the failure ``(failure) -> bool``,
    :returns: A function that calls the handler only if the condition returns True.
    """
    if condition is _match_all:
        return handler

    def _handler(failure: Failure) -> None:
        if condition(failure):
            handler(failure)
    return _handler


def combine(handlers: Union[FailureHandler, Tuple[FailureHandler, ...]], /) -> FailureHandler:
    """Merge all handlers into a single function that calls them the same order they were provided."""
    if isinstance(handlers, tuple):
        if not handlers:
            raise _invalid(TypeError, "Cannot define an empty tuple as failure handler")
        if len(handlers) > 1:
            def handle(failure: Failure) -> None:
                for handler in handlers:  # type: ignore[union-attr]
                    handler(failure)
            handlers = tuple(map(_validate_handler, handlers))
            return handle
        handlers = handlers[0]
    return _validate_handler(handlers)


class Handler:
    """
    Handler object combines multiple filtered or unfiltered failure handlers
    together as a single failure handler, allowing the creation of complex
    failure handlers.

    The handler is also a context manager, used with the ``with`` statement,
    it captures and automatically handles any raised FailureException.
    """
    __slots__ = '__handler',
    __handler: FailureHandler

    def __init__(self, *args: Union[FailureHandler, Tuple[HandlerOrHandlers, Filters]]):
        """
        The handler constructor optionally takes one or multiple failure handing functions
        (with signature (Failure)->None), the handlers also can be filtered to handle only
        a targeted group of failures.

        To pass a filtered handler, put it inside a tuple followed with one or multiple filter
        like (func, (filter1, filter2, ...)), so func will be called only if the failure matches
        any of filter1, filter2, ...

        Filtered handlers can also be more specific by combining filters like (func, (f1, f2), f3, (f4, f5, f6)),
        so func will only handle failures that match the filters: (f1 AND f2) OR f3 OR (f4 AND f5 AND f6)

        :param args: A sequence of either func, (func, (filter, filter, ...)) or (func, ((filter, filter), (...), ...))
        """
        _handlers = []
        for arg in args:
            if isinstance(arg, tuple):
                try:
                    _han, _fts = arg
                except ValueError:
                    raise _invalid(ValueError, "The tuple of filtered handler must contain exactly two elements;"
                                               "(handler, filter) or (handler, (filter, filter, ...) "
                                               "or ((handler1, handler2, ...), filter)")
                arg = filtered(combine(_han), filters(_fts))
            _handlers.append(arg)
        self.__handler = combine(tuple(_handlers)) if _handlers else print_failure

    def __call__(self, failure: Failure, /) -> None:
        """Handles the failure by calling the internal handler"""
        self.__handler(failure)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None) -> bool:
        if exc_type is None:
            return True
        elif issubclass(exc_type, FailureException):
            self(exc_val.failure)
            return True
        return False

    def from_reporter(self, reporter: Reporter) -> None:
        """
        Handles every failure registered by the reporter.

        :param reporter: Reporter that holds failures
        :return: None
        """
        for failure in reporter.failures:
            self.__handler(failure)
