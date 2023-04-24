"""failures.handler module implements the failure handling tools"""
import re
import abc
from typing import Pattern, List, Literal, Generator
from datetime import datetime
from contextlib import contextmanager
try:
    import colorama
except ImportError:
    colorama = None
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

from .core import (Failure, FailureHandler, FailureException, Filters,
                   SupportedFilters, FailureFilter, ExceptionTypes)


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
        return isinstance(failure.error, self.exc_type)


def _match_all(_: Failure, /) -> Literal[True]:
    """Matches all the failures"""
    return True


def _make_filter(spec: SupportedFilters) -> FailureFilter:
    """Creates a filter from specification"""
    if spec == '*' or spec is Exception:
        return _match_all  # optimising match
    if isinstance(spec, str):
        if '*' in spec:
            return FailureLabelPatternMatch(spec)
        return FailureLabelMatch(spec)
    if isinstance(spec, type) and issubclass(spec, Exception):
        return FailureExceptionMatch(spec)
    raise TypeError(f"Unsupported filter type {type(spec).__name__!r}")


if __debug__:
    def _validate_handler(obj: FailureHandler) -> FailureHandler:
        """Validates the failure handler function"""
        if not callable(obj):
            raise TypeError("the handler must be a callable with signature: (Failure) -> None")
        return obj
else:
    def _validate_handler(obj: FailureHandler) -> FailureHandler:
        return obj


def filtered(handler: FailureHandler, *filters: Filters) -> FailureHandler:
    """Creates a conditional handler based on the specified filters"""
    filters_: List[FailureFilter] = []
    for filter_ in filters:
        if isinstance(filter_, tuple):
            _len = len(filter_)
            if _len > 1:
                fls = tuple(map(_make_filter, filter_))
                filters_.append(lambda f: all((flt(f) for flt in fls)))
                continue
            elif _len == 1:
                filter_ = filters[0]
            else:
                continue
        filters_.append(_make_filter(filter_))
    _len = len(filters_)
    if _len > 1:
        condition = lambda f: any((flt(f) for flt in filters_))
    elif _len == 1:
        condition = filters_[0]
    else:
        raise ValueError("At least one filter is required")
    handler = _validate_handler(handler)

    def _handle(failure: Failure, /) -> None:
        if condition(failure):
            return handler(failure)
    return _handle


def combine(handler: FailureHandler, *handlers: FailureHandler) -> FailureHandler:
    """Combines multiple handlers into a handler that calls them in the same order"""
    if not handlers:
        return _validate_handler(handler)

    def _handle(failure: Failure, /) -> None:
        for _handler in _handlers:
            _handler(failure)
    _handlers = list(map(_validate_handler, (handler, *handlers)))
    return _handle


@contextmanager
def handle(handler: FailureHandler = print_failure) -> Generator[None, None, None]:
    """Context manager that captures and handles failures"""
    try:
        yield
    except FailureException as err:
        for failure in (err.failure, *err.reporter.failures):
            handler(failure)
