"""failures.core module implements the core utilities and object definition like the Reporter and scope..."""
import re
import sys
import enum
import asyncio
import functools
import inspect
from types import TracebackType
from functools import cached_property
from typing import (Optional, Type, List, Dict, Any, overload, Callable,
                    Awaitable, NamedTuple, TypeVar, Union, Pattern, Tuple)

if sys.version_info.minor >= 10:
    from typing import ParamSpec, TypeAlias
else:
    from typing_extensions import ParamSpec, TypeAlias


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
    """Specifies three levels to react to failures"""
    OPTIONAL = 0    # ignores the failure
    NORMAL = 1      # reports the failure
    REQUIRED = 2    # raises the failure


# Severity options shorthands
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


class Failure(NamedTuple):
    """Container that holds a failure information"""
    source: str
    error: Exception
    details: Dict[str, Any]
    severity: Severity = NORMAL


class FailureException(Exception):
    """Wraps error to keep track of labeled sources"""
    source: str
    error: Exception
    reporter: Optional['Reporter']
    details: Dict[str, Any]

    def __init__(self, source: str, error: Exception, reporter: 'Reporter' = None, **details):
        self.source = source
        self.error = error
        self.reporter = reporter
        self.details = details

    @property
    def failure(self) -> Failure:
        """Gets the failure information"""
        return Failure(self.source, self.error, self.details, REQUIRED)


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

    def __init__(self, name: str, /, severity: Severity = NORMAL) -> None:
        """
        :param name: The label for the current reporter (mandatory)
        :param severity: Specifies the operation type: OPTIONAL, NORMAL (default) or REQUIRED
        """
        if __debug__:
            # Validation is only evaluated when run without the -O or -OO python flag
            if not isinstance(name, str):
                raise _invalid(TypeError, "label must be a string")
            elif not NamePattern.match(name):
                raise _invalid(ValueError, f"invalid label: {name!r}")
            if not isinstance(severity, Severity):
                raise TypeError("'severity' can either be OPTIONAL, NORMAL or REQUIRED")
        self.__name = name
        self.__severity = severity

    def __call__(self, name: str, /, severity: Severity = NORMAL) -> 'Reporter':
        """
        Creates a reporter child bound to the current one.

        :param name: The label for the current reporter (mandatory)
        :param severity: Specifies the operation type: OPTIONAL, NORMAL (default) or REQUIRED
        :returns: New reporter object
        """
        return ReporterChild(name, self, severity)

    def __repr__(self) -> str:
        return f'Reporter({self.label!r}, {self.severity.name})'

    @property
    def parent(self) -> Optional['Reporter']:
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

    @property
    def severity(self) -> Severity:
        """Gets the severity level of the current reporter."""
        return self.__severity

    def report(self, error: Exception, **details) -> None:
        """
        The reporter treats the failure depending on the severity flag,

        :param error: A regular exception or a pre-labeled failure
        :param details: Any additional details to be reported with the failure
        :returns: None
        """
        source = self.label
        severity = self.severity
        if severity is OPTIONAL:
            # Ignores the failure
            return
        if isinstance(error, FailureException):
            # Unwrap labeled failures
            source = _join(source, error.source)
            details = {**details, **error.details}
            error = error.error
        if severity is REQUIRED:
            # Raises the failure as exception
            raise FailureException(source, error, self, **details)
        self.failures.append(Failure(source, error, details))

    def handle(self, handler: FailureHandler) -> None:
        """Calls the handler function with each registered failure"""
        for failure in self.failures:
            handler(failure)

    def safe(self, func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls the function in a safe context and reports the failure if it occurs

        :param func: The function to be called in a safe context
        :param args: Any positional arguments expected by func
        :param kwargs: Any keyword arguments expected by func
        :returns: The returned value of func or None if it fails
        """
        try:
            return func(*args, **kwargs)
        except Exception as err:
            self.report(err)

    async def safe_async(self, func: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        """
        Calls the coroutine function in a safe context and reports the failure if it occurs

        :param func: The coroutine function to be called in a safe context
        :param args: Any positional arguments expected by func
        :param kwargs: Any keyword arguments expected by func
        :returns: The returned value of func or None if it fails
        """
        try:
            return await func(*args, **kwargs)
        except Exception as err:
            self.report(err)


class ReporterChild(Reporter):
    __slots__ = ('__parent',)
    __parent: Reporter

    def __init__(self, name: str, /, parent: Reporter, severity: Severity = NORMAL) -> None:
        if __debug__:
            if not isinstance(parent, Reporter):
                raise TypeError("'parent' must be instance of Reporter")
        Reporter.__init__(self, name, severity)
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


@overload
def scoped(function: FunctionVar, /) -> FunctionVar: ...
@overload
def scoped(*, name: str = ...) -> Callable[[FunctionVar], FunctionVar]: ...


def scoped(function: FunctionVar = None, /, *, name: str = None):
    """
    A decorator used over functions to add a labeled failures scope,
    by default, the label will be the function's name, but
    it could be overridden with a custom label
    """
    def decorator(func: FunctionVar, /) -> FunctionVar:
        """Ready to used 'failures.scoped' decorator"""
        if not callable(func):
            raise _invalid(TypeError, "failures.scoped decorator expects a functions")
        name_ = name if name is not None else func.__name__
        is_async = asyncio.iscoroutinefunction(func)
        spec = inspect.getfullargspec(func)
        rep_name = 'reporter'
        for idx, _arg in enumerate(spec.args):
            if _arg != rep_name:
                continue

            def _new_args(args, rep):
                _args = list(args)
                _args[idx] = rep
                return _args
            idx = spec.args.index(rep_name)
            if is_async:
                async def wrapper(*args, **kwargs):
                    with scope(name_, args[idx]) as rep:
                        return await func(*_new_args(args, rep), **kwargs)
            else:
                def wrapper(*args, **kwargs):
                    with scope(name_, args[idx]) as rep:
                        return func(*_new_args(args, rep), **kwargs)
            break
        else:
            if rep_name in spec.kwonlyargs:
                if is_async:
                    async def wrapper(*args, **kwargs):
                        with scope(name_, kwargs.pop(rep_name)) as rep:
                            kwargs[rep_name] = rep
                            return await func(*args, **kwargs)
                else:
                    def wrapper(*args, **kwargs):
                        with scope(name_, kwargs.pop(rep_name)) as rep:
                            kwargs[rep_name] = rep
                            return func(*args, **kwargs)
            elif is_async:
                async def wrapper(*args, **kwargs):
                    with scope(name_):
                        return await func(*args, **kwargs)
            else:
                def wrapper(*args, **kwargs):
                    with scope(name_):
                        return func(*args, **kwargs)
        wrapper.__signature__ = inspect.signature(func)
        return functools.update_wrapper(wrapper, func)
    return decorator if function is None else decorator(function)
