"""This module contains implementation of the core elements of the 'failures' library"""
import inspect
import re
import types
import functools
from warnings import warn
from typing import (Union, Tuple, Optional, overload, TypeVar, Type, List, Generator, Set, Protocol, Callable, cast)

# https://github.com/python/typeshed/pull/9850
from typing_extensions import (  # type: ignore[attr-defined]
    Self,
    TypeAlias,
    ParamSpec,
    deprecated
)

from ._print import print_failure


# Type Aliases
FailureOrFailures: TypeAlias = Union['Failure', 'Failures']
AnyException = TypeVar('AnyException', bound=BaseException)
AnyValue = TypeVar('AnyValue')
FuncArgs = ParamSpec('FuncArgs')
FailureFilter: TypeAlias = Union[Type[Exception]]  # will be adding source identifier in next version
FailureFilters: TypeAlias = Tuple[FailureFilter, ...]
FunctionVar = TypeVar('FunctionVar', bound=Callable)
SupportedFailureHandler: TypeAlias = Union['FailureHandler', 'Handler']


class FailureHandler(Protocol):  # signature of a failure handler function
    def __call__(self, source: str, error: Exception, **kwargs) -> None:
        """
        Takes two positional arguments; the source of failure and the error that caused it.
        kwargs in the other hand will hold additional details in the future
        """


# Regex Pre-compiled patterns
NamePattern = re.compile(r'^(\w+(\[\w+]|\(\w+\))?)+([-.](\w+(\[\w+]|\(\w+\))?))*$')


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


def _validate_label(label: str) -> str:
    """Validates the name and returns it"""
    if not isinstance(label, str):
        raise _invalid(TypeError, "label must be a string")
    elif not NamePattern.match(label):
        raise _invalid(ValueError, f"invalid label: {label!r}")
    return label


@overload
def _validate_handler(handler: None) -> None: ...
@overload
def _validate_handler(handler: Union[FailureHandler, 'Handler']) -> 'Handler': ...


def _validate_handler(handler: Union[FailureHandler, 'Handler', None]) -> Optional['Handler']:
    """Validates the failure handler function"""
    if handler is None:
        return None
    elif isinstance(handler, Handler):
        return handler
    return handler_(handler)


def _label_failure(error: Union[Exception, 'Failure'], /, label: str) -> 'Failure':
    """
    Helper functions that labels failures or error,
    (No validation is performed for optimization)
    """
    if isinstance(error, (Failure, Failures)):
        return error.within(label)
    return Failure(label, error)


class Failure(Exception):
    """Wraps error to keep track of labeled sources"""

    def __init__(self, source: str, error: Exception):
        self.source: str = source
        self.error: Exception = error

    def within(self, name: str) -> Self:
        """Prepends the label (name) to the failure source name.source.(...)"""
        self.source = _join(name, self.source)
        return self


class Failures(Failure):
    """Wraps multiple failures as a group"""

    def __init__(self, *failures: Failure) -> None:
        self.__failures: List[Failure] = list(failures)

    @property
    def failures(self) -> Generator[Failure, None, None]:
        """Returns an iterator over registered failures"""
        for failure in self.__failures:
            if isinstance(failure, Failures):
                yield from failure.failures
            elif isinstance(failure, Failure):
                yield failure

    @deprecated("Failures.add method will be removed in next major releases")
    def add(self, failure: Failure) -> None:
        """Adds a new failure to the registered failures list"""
        self.__failures.append(failure)

    def within(self, name: str) -> Self:
        """Prepends the label (name) to all the failures' sources"""
        self.__failures = [failure.within(name) for failure in self.__failures]
        return self


class Handler:
    """
    Custom failure handler that takes additional filtering information,
    the handler takes care of recursively fetching failures within a failure group.

    (Note: The handler object is not directly created by the used, but through the 'handler' function)
    """
    __slots__ = ("handler_function", "ignore", "propagate")

    handler_function: FailureHandler
    ignore: FailureFilters
    propagate: FailureFilters

    def __init__(self, handler: FailureHandler, /, ignore: FailureFilters, propagate: FailureFilters) -> None:
        """
        :param handler: function to be called with the failure details
        :param ignore: a tuple of exception types to be ignored
        :param propagate:  a tuple of exception types to be reraised
        """
        self.handler_function = handler
        self.ignore = ignore
        self.propagate = propagate

    @staticmethod
    def _match(specification: FailureFilters, failure: FailureOrFailures) -> bool:
        """Detects if the failure matches the specification"""
        return bool(specification) and isinstance(failure.error, specification)

    def __call__(self, failure: FailureOrFailures) -> None:
        if isinstance(failure, Failures):
            for failure in failure.failures:
                self(failure)
        elif isinstance(failure, Failure):
            source, error = failure.source, failure.error
            if self._match(self.ignore, failure):
                return
            elif self._match(self.propagate, failure):
                raise failure from None
            self.handler_function(source, error)


def _prepare_filter_(flt: Union[FailureFilters, FailureFilter, None]) -> FailureFilters:
    """Ensures that filters are a tuple"""
    if flt is None:
        return ()
    elif not isinstance(flt, tuple):
        return (flt,)
    return flt


def handler_(   # underscored in module scope to allow un-shadowed used of the name 'handler'
        handler: SupportedFailureHandler = print_failure, /, *,
        ignore: Union[FailureFilters, FailureFilter, None] = None,
        propagate: Union[FailureFilters, FailureFilter, None] = None
) -> Handler:
    """
    Creates a custom failure handler that takes additional filtering information.

    :param handler: function to be called with the failure details (or handler object)
    :param ignore: an exception type or a tuple of exception types to be ignored
    :param propagate:  an exception type or a tuple of exception types to be reraised
    """
    ignore_ = _prepare_filter_(ignore)
    propagate_ = _prepare_filter_(propagate)
    while isinstance(handler, Handler):
        # combines handler info
        ignore_ = *handler.ignore, *ignore_
        propagate_ = *handler.propagate, *propagate_
        handler = handler.handler_function
    if not callable(handler):
        raise _invalid(TypeError, "failure handling function must be a callable object")
    #                       optimizes filters and remove redundancy
    return Handler(handler, tuple(set(ignore_)), tuple(set(propagate_)))


class Scope:
    """
    Scope is an object that holds context information and used to catch,
    label and handle any failures withing its scope using the handler object if present,
    or re-raises the labeled failure to be captured by an outer layer scope.

    (Note: The scope object is not directly created by the used, but through the 'scope' function)
    """
    __slots__ = ('__name', '__qualname', '__subs', '__failures', '__handler', '__origin')

    def __init__(self, name: str, handler: Handler = None, /, root: 'Scope' = None, origin: 'Scope' = None) -> None:
        """
        :param name: the label of the context (Mandatory)
        :param handler: the handler object (Optional, default = None)
        :param root: The scope object that created this one (Optional)
        :param origin: The scope object that created this one and all it's parents (Optional)
        """
        self.__name: str = name
        self.__qualname: str = _join(root.qualname, name) if isinstance(root, Scope) else name
        self.__subs: Set[str] = set()
        self.__failures: List[Failure] = []
        self.__handler: Optional[Handler] = handler
        self.__origin: Optional[Scope] = origin

    @overload
    def __call__(self, name: str, /) -> 'Scope': ...
    @overload
    def __call__(self, name: str, handler: SupportedFailureHandler, /) -> 'Scope': ...

    def __call__(self, name: str, handler: SupportedFailureHandler = None, /) -> 'Scope':
        """
        Creates a sub scope object that keep reference to this one as parent.

        :param name: The label of the new sub scope (Mandatory)
        :param handler: The handler function or Handler object (Optional, default = self.handler)
        """
        _name = _validate_label(name)
        _handler = self.__handler if (handler is None) else _validate_handler(handler)
        if _name in self.__subs:
            warn(UserWarning(f"{_name!r} label has been used previously"), stacklevel=1, source=self)
        else:
            self.__subs.add(_name)
        return Scope(_name, _handler, root=self, origin=(self.__origin or self))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _err_type, error, _err_tb) -> bool:
        if (isinstance(error, BaseException) and not isinstance(error, Exception)) or _is_validation_error(error):
            # Avoid handling higher exceptions (like KeyboardInterrupt)
            # Or package validation error that are meant to be raised
            return False
        self.handle(error)
        return True

    @property
    def name(self) -> str:
        """The scope label (read-only)"""
        return self.__name

    @property
    def qualname(self) -> str:
        """The scope fully qualified label (read-only)"""
        return self.__qualname

    @property
    def handler(self) -> Optional[Handler]:
        """The handler used by this scope or None (read-only)"""
        return self.__handler

    def add_failure(self, error: Union[Exception, Failure], /, label: str = None) -> None:
        """
        Registers the error with an optional label to be handled later.

        :param error: exception or a pre-wrapped failure (Mandatory)
        :param label: if a label is passed, it will be prepended to the failure's source (Optional)
        """
        if not isinstance(error, Exception):
            raise _invalid(TypeError, f"invalid error type {type(error).__name__!r}")
        if label is not None:
            error = _label_failure(error, _validate_label(label))
        if not getattr(error, '__from_child_scope__', False):
            error = _label_failure(error, self.__qualname)
        if self.__origin is not None:
            setattr(error, '__from_child_scope__', True)
            self.__origin.add_failure(error)
        else:
            self.__failures.append(cast(Failure, error))

    def handle(self, error: Union[Exception, Failures, Failure] = None) -> None:
        """
        Handles all registered failures (and optionally also the argument) if a handler
        is passed to the scope, otherwise, gathers all the failures and raises
        them to the higher scope to be captured.

        :param error: either a failure, a failures or a normal exception object (Optional)
        """
        if isinstance(error, Exception):
            self.add_failure(error)
        if not self.__failures:
            return  # Nothing to handle
        failure = Failures(*self.__failures) if len(self.__failures) > 1 else self.__failures[0]  # optimization
        if self.__handler is None:
            raise failure
        self.__handler(failure)
        self.__failures = []


def scope(name: str, handler: SupportedFailureHandler = None) -> Scope:
    """
    Creates a labeled failure's scope object with and optional handler,
    if the handler is provided, failures within scope will be handled locally,
    otherwise the error will be raised with a label.

    :param name: the label to mark inner scope failures (Mandatory)
    :param handler: the handler function or handler object or None (Optional, default = None)

    :return: New scope object
    """
    return Scope(_validate_label(name), _validate_handler(handler))


@overload
def scoped(function: FunctionVar, /) -> FunctionVar: ...
@overload
def scoped(*, name: str = ..., handler: SupportedFailureHandler = ...) -> Callable[[FunctionVar], FunctionVar]: ...


def scoped(func: FunctionVar = None, /, *, name: str = None, handler: SupportedFailureHandler = None):
    """
    A decorator used over functions to add a labeled failures scope,
    by default, the label will be the function's name, but
    it could be overridden with a custom label.

    The decorator also takes an optional local failure handler.
    """
    def decorator(function: Callable[FuncArgs, AnyValue], /) -> Callable[FuncArgs, AnyValue]:
        """Ready to used 'failures.scoped' decorator"""
        if not isinstance(function, types.FunctionType):
            raise _invalid(TypeError, "failures.scoped only supports decorating standard functions")

        nonlocal name
        if name is None:
            name = function.__name__

        def wrapper(*args: FuncArgs.args, **kwargs: FuncArgs.kwargs) -> AnyValue:
            with scope(name, handler):
                return function(*args, **kwargs)
        wrapper.__signature__ = inspect.signature(function)
        return functools.update_wrapper(wrapper, function)
    if func is None:
        return decorator
    return decorator(func)
