"""
core.py module contains the base library elements, the main ones are ``Reporter`` and ``Failure``;
the first is used to collect failures between a series of operations, and the second is a wrapper
that encapsulates failure details.
"""
import re
from functools import cached_property
from typing import Optional, Type, List, Dict, Any, Callable, Awaitable, NamedTuple, TypeVar

from typing_extensions import ParamSpec, Self


# Type Aliases
T = TypeVar('T')
P = ParamSpec('P')
FunctionVar = TypeVar('FunctionVar', bound=Callable)
AnyException = TypeVar('AnyException', bound=BaseException)

# Reporter name pattern
NamePattern = re.compile(r'^(\w+(\[\w+]|\(\w+\))?)+([-.](\w+(\[\w+]|\(\w+\))?))*$')


class Failure(NamedTuple):
    """
    Failure is an object that encapsulates the error
    together with its source and additional details.

    :param source: The dot separated labels leading to where the failure occurred,
    :param error: The actual exception that caused the failure,
    :param details: Additional user added metadata.
    """
    source: str
    error: Exception
    details: Dict[str, Any]


class FailureException(Exception):
    """
    FailureException is an exception that wraps failure details to be raised
    and captured by the caller without passing reporter objects between functions

    The exception also keeps reference to the reporter object that raised it
    to get any registered failures and also avoid name duplication when
    the outer layer reporter captures the exception, as a rule the reporter
    that captures it only prepends its label if it wasn't already prepended,
    this is done by checking if the source reporter shares the same root.
    """
    failure: Failure
    reporter: 'Reporter'

    def __init__(self, failure: Failure, reporter: 'Reporter') -> None:
        """
        :param failure: Failure object containing the source, error and details
        :param reporter: The reporter that raised this exception
        """
        self.failure = failure
        self.reporter = reporter

    @property
    def source(self) -> str:
        """Gets the source of the failure"""
        return self.failure.source

    @property
    def error(self) -> Exception:
        """Gets the error that caused the failure"""
        return self.failure.error

    @property
    def details(self) -> Dict[str, Any]:
        """Gets the failure additional details"""
        return self.failure.details


def _join(label1: str, label2: str) -> str:
    """Joins two labels together with a dot"""
    return label1 + '.' + label2


def _invalid(err_type: Type[AnyException], *args) -> AnyException:
    """Marks an error as a package validation error and returns it"""
    error = err_type(*args)
    setattr(error, "__validation_error__", True)
    return error


def _is_validation_error(error: Exception) -> bool:
    """Checks if the error is a package validation error"""
    return getattr(error, "__validation_error__", False)


class Reporter:
    """
    Reporters are objects used to collect failures (errors) between function calls
    and add context metadata and details, and pinpoint the source by labels.
    """
    __slots__ = ('__name', '__failures', '_details', '__dict__')
    __name: str
    _details: Dict[str, Any]
    __failures: List[Failure]

    def __init__(self, name: str, /, **details) -> None:
        """
        :param name: The label for the current reporter (mandatory)
        :param details: Additional details bound to the reporter
        """
        if __debug__:
            # Validation is only evaluated when run without the -O or -OO python flag
            if not isinstance(name, str):
                raise _invalid(TypeError, "label must be a string")
            elif not NamePattern.match(name):
                raise _invalid(ValueError, f"invalid label: {name!r}")
        self.__name = name
        self._details = details

    def __call__(self, name: str, /, **details) -> '_ReporterChild':
        """
        Creates a reporter child bound to the current one.

        :param name: The label for the current reporter (mandatory)
        :param details: Additional details bound to the reporter
        :returns: New reporter object
        """
        return _ReporterChild(name, self, **details)

    def __repr__(self) -> str:
        return f'Reporter({self.label!r})'

    @property
    def parent(self) -> Optional['Reporter']:
        """Gets the reporter's parent if this was derived from one, or None instead"""
        return None

    @property
    def root(self) -> 'Reporter':
        """Gets this reporter as it's the first one"""
        return self

    @property
    def name(self) -> str:
        """Gets the reporter's name (without parent names)"""
        return self.__name

    @property
    def label(self) -> str:
        """Gets the name of the current reporter"""
        return self.__name

    @property
    def details(self) -> Dict[str, Any]:
        """Gets additional details bound to the reporter"""
        return self._details

    @property
    def failures(self) -> List[Failure]:
        """Gets the failures' list (mutable)"""
        try:
            return self.__failures
        except AttributeError:
            self.__failures = []
            return self.__failures

    def failure(self, error: Exception, **details) -> Failure:
        """Creates a failure from error, details and reporter's information"""
        if isinstance(error, FailureException):
            # Unwrap Failure exception
            if error.reporter.root is self.root:
                # From a bound reporter
                source = error.source
                details = error.details
                error = error.error
            else:
                # From an unbound reporter
                source = _join(self.label, error.source)
                details = {**details, **error.details}
                self.failures.extend(error.reporter.failures)
                error = error.error
        else:
            source = self.label
        return Failure(source, error, {**self.details, **details})

    def report(self, error: Exception, **details) -> None:
        """
        Registers the failure into the shared failures list

        :param error: Regular Exception or FailureException
        :param details: Any additional details to be reported with the failure
        :returns: None
        """
        self.failures.append(self.failure(error, **details))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _err_type, error: BaseException, _err_tb):
        if isinstance(error, Exception) and not _is_validation_error(error):
            raise FailureException(self.failure(error), self) from None
        # Avoid handling higher exceptions (like BaseException, KeyboardInterrupt, ...)
        # Or module validation errors that must be raised

    def safe(self, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls func with args and kwargs inside a safe block and returns its result if
        it succeeds, or returns None and report the failure otherwise.
        """
        try:
            return func(*args, **kwargs)
        except Exception as err:
            self.report(err)
            return None

    async def safe_async(self, func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls await func with args and kwargs inside a safe block and returns its result if
        it succeeds, or returns None and report the failure otherwise.
        """
        try:
            return await func(*args, **kwargs)
        except Exception as err:
            self.report(err)
            return None

    @staticmethod
    def optional(func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls func with args and kwargs inside a safe block and returns its result if
        it succeeds, or returns None and ignores the failure otherwise.
        """
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    @staticmethod
    async def optional_async(func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls await func with args and kwargs inside a safe block and returns its result if
        it succeeds, or returns None and ignores the failure otherwise.
        """
        try:
            return await func(*args, **kwargs)
        except Exception:
            return None

    def required(self, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Calls func with args and kwargs inside a safe block and returns its result if
        it succeeds, or raises a labeled failure otherwise.
        """
        with self:
            return func(*args, **kwargs)

    async def required_async(self, func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Calls await func with args and kwargs inside a safe block and returns its result if
        it succeeds, or raises a labeled failure otherwise.
        """
        with self:
            return await func(*args, **kwargs)


class _ReporterChild(Reporter):
    __slots__ = ('__parent',)
    __parent: Reporter

    def __init__(self, name: str, /, parent: Reporter, **details: Dict[str, Any]) -> None:
        if __debug__:
            if not isinstance(parent, Reporter):
                raise TypeError("'parent' must be instance of Reporter")
        Reporter.__init__(self, name, **details)
        self.__parent = parent

    @property
    def parent(self) -> Reporter:
        """Gets the reporter that created this one"""
        return self.__parent

    @cached_property
    def root(self) -> Reporter:
        """Gets the first parent of this reporter"""
        return self.__parent.root

    @cached_property
    def label(self) -> str:
        """Gets the hierarchical name of this reporter"""
        return _join(self.parent.label, self.name)

    @cached_property
    def details(self) -> Dict[str, Any]:
        """Gets reporter's context details combined with its parents'"""
        return {**self.parent.details, **self._details}

    @property
    def failures(self) -> List[Failure]:
        """Gets the root's failures list (mutable)"""
        return self.root.failures
