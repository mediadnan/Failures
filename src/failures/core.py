"""failures.core module implements the core utilities and object definition like the Reporter and scope..."""
import re
import enum
from types import TracebackType
from functools import cached_property
from typing import (Optional, Type, List, Dict, Any, Callable,
                    Awaitable, NamedTuple, TypeVar, Union, Pattern, Tuple)

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


# Type Aliases
T = TypeVar('T')
P = ParamSpec('P')
FunctionVar = TypeVar('FunctionVar', bound=Callable)
FailureHandler: TypeAlias = Callable[['Failure'], None]
SupportedFilters: TypeAlias = Union[str, Pattern[str], Type[Exception], 'Severity']
FailureFilter: TypeAlias = Callable[['Failure'], bool]
ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]
Filters: TypeAlias = Union[SupportedFilters, Tuple[SupportedFilters, ...]]
AnyException = TypeVar('AnyException', bound=BaseException)

NamePattern = re.compile(r'^(\w+(\[\w+]|\(\w+\))?)+([-.](\w+(\[\w+]|\(\w+\))?))*$')


class Severity(enum.Enum):
    """Specify three levels to react to failures"""
    OPTIONAL = 0  # ignores the failure
    NORMAL = 1  # reports the failure
    REQUIRED = 2  # raises the failure


# Severity options shorthands
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


class Failure(NamedTuple):
    """Container that holds failure information"""
    source: str
    error: Exception
    details: Dict[str, Any]


class FailureException(Exception):
    """Wraps error to keep track of labeled sources"""
    failure: Failure
    reporter: 'Reporter'

    def __init__(self, failure: Failure, reporter: 'Reporter') -> None:
        self.failure = failure
        self.reporter = reporter

    @property
    def source(self) -> str:
        return self.failure.source

    @property
    def error(self) -> Exception:
        return self.failure.error

    @property
    def details(self) -> Dict[str, Any]:
        return self.failure.details


def _join(label1: str, label2: str) -> str:
    """Joining two labels together"""
    # behaviour defined in one single place
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
    The reporter holds failures between function calls and generates
    sub reporters to pinpoint the source of each failure.

    The reporter comes in three flavours;
        - Reporter for NORMAL operations stores failures in a shared list to be handled later,
        - Reporter for OPTIONAL operations just ignores failures, useful for expected ones,
        - Reporter for REQUIRED operations raises the failure to ensure that next code blocks
          are not evaluated until the failure is explicitly handled.
    """
    __slots__ = ('__name', '__failures', '__dict__')
    __name: str
    __failures: List[Failure]

    def __init__(self, name: str, /) -> None:
        """
        :param name: The label for the current reporter (mandatory)
        """
        if __debug__:
            # Validation is only evaluated when run without the -O or -OO python flag
            if not isinstance(name, str):
                raise _invalid(TypeError, "label must be a string")
            elif not NamePattern.match(name):
                raise _invalid(ValueError, f"invalid label: {name!r}")
        self.__name = name

    def __call__(self, name: str, /) -> 'ReporterChild':
        """
        Creates a reporter child bound to the current one.

        :param name: The label for the current reporter (mandatory)
        :returns: New reporter object
        """
        return ReporterChild(name, self)

    def __repr__(self) -> str:
        return f'Reporter({self.label!r})'

    @property
    def parent(self) -> None:
        """Gets nothing as this reporter has no parent"""
        return

    @property
    def root(self) -> 'Reporter':
        """Gets this reporter as it's the first one"""
        return self

    @property
    def name(self) -> str:
        """Gets the reporter's name (without parent names)."""
        return self.__name

    @property
    def label(self) -> str:
        """Gets the name of the current reporter"""
        return self.__name

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
        source = self.label
        if isinstance(error, FailureException) and error.reporter.root is not self.root:
            # Unwrap labeled failures
            source = _join(source, error.source)
            details = {**details, **error.details}
            error = error.error
        return Failure(source, error, details)

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

    def __exit__(
            self,
            _err_type: Type[BaseException] = None,
            error: BaseException = None,
            _err_tb: TracebackType = None
    ) -> bool:
        if error is None:
            return True
        elif isinstance(error, Exception):
            raise FailureException(self.failure(error), self)
        # Avoid handling higher exceptions (like BaseException, KeyboardInterrupt, ...)
        # Or module validation errors that must be raised
        return False

    def safe(self, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or returns None and report the failure otherwise.
        """
        try:
            return func(*args, **kwargs)
        except Exception as err:
            self.report(err)

    async def safe_async(self, func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls await func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or returns None and report the failure otherwise.
        """
        try:
            return await func(*args, **kwargs)
        except Exception as err:
            self.report(err)

    @staticmethod
    def optional(func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or returns None and ignores the failure otherwise.
        """
        try:
            return func(*args, **kwargs)
        except Exception:
            return

    @staticmethod
    async def optional_async(func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls await func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or returns None and ignores the failure otherwise.
        """
        try:
            return await func(*args, **kwargs)
        except Exception:
            return

    def required(self, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Calls func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or raises a labeled failure otherwise.
        """
        with self:
            return func(*args, **kwargs)

    async def required_async(self, func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Calls await func(*args, **kwargs) inside a safe block and returns its result if
        it succeeds, or raises a labeled failure otherwise.
        """
        with self:
            return await func(*args, **kwargs)


class ReporterChild(Reporter):
    __slots__ = ('__parent',)
    __parent: Reporter

    def __init__(self, name: str, /, parent: Reporter) -> None:
        if __debug__:
            if not isinstance(parent, Reporter):
                raise TypeError("'parent' must be instance of Reporter")
        Reporter.__init__(self, name)
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

    @property
    def failures(self) -> List[Failure]:
        """Gets the root's failures list (mutable)"""
        return self.root.failures


class scope:
    """
    Scope is a context manager object that capture error or pre-labeled failures and prepends its label
    then re-raise it, any error within the scope will be labeled and raised with a REQUIRED flag
    to prevent the execution of next blocks avoiding name errors or unexpected bugs
    """
    __slots__ = ('__reporter', '__details')
    __reporter: Reporter
    __details: Dict[str, Any]

    def __init__(self, name: str, /, reporter: Reporter = None, **details) -> None:
        """
        :param name: The label for the current scope (mandatory)
        :param reporter: The reported to be passed inside the scope (optional)
        :param details: Any additional information to be reported (optional)
        """
        if __debug__:
            if not (reporter is None or isinstance(reporter, Reporter)):
                raise TypeError("'reporter' must be instance of Reporter")
        self.__reporter = (reporter or Reporter)(name, REQUIRED)
        self.__details = details

    def __enter__(self) -> Reporter:
        return self.__reporter

    def __exit__(self,
                 _err_type: Type[BaseException] = None,
                 error: BaseException = None,
                 _err_tb: TracebackType = None) -> bool:
        if error is None:
            return True
        elif isinstance(error, Exception):
            self.__reporter.report(error, **self.__details)
        # Avoid handling higher exceptions (like BaseException, KeyboardInterrupt, ...)
        # Or module validation errors that must be raised
        return False
