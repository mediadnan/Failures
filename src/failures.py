"""
Failures is a python module that contains tools for
labeling nested errors and pinpoint their source.
"""
import importlib
import pkgutil
import re
from typing import Optional, List, Set, Generator, Union, Type, Tuple, overload, TypeVar, cast, Callable

__version__ = "0.1.0"
__all__ = ("FailureHandler", "Failure", "Failures", "scope", "handle")

# signature of a failure handler function
FailureHandler = Callable[[str, Exception], None]

default_handler: Optional[FailureHandler] = None


def _load_plugins_default_handler() -> None:
    for finder, name, is_pkg in pkgutil.iter_modules():
        if not name.startswith('failures_handler_'):
            continue
        module = importlib.import_module(name)
        if 'handler' in vars(module):
            global default_handler
            default_handler = getattr(module, 'handler')
            break


_load_plugins_default_handler()


class Failure(Exception):
    """Wraps error to keep track of labeled sources"""

    def __init__(self, source: str, error: Exception):
        self.source: str = source
        self.error: Exception = error

    def within(self, name: str) -> "Failure":
        """Adds outer label"""
        self.source = name + "." + self.source
        return self


class Failures(Failure):
    """Wraps multiple failures as a group"""

    def __init__(self, *failures: Failure) -> None:
        self.__failures: List[Failure] = list(failures)

    @property
    def failures(self) -> Generator[Failure, None, None]:
        """Returns an iterator over registered failures"""
        yield from self.__failures

    def add(self, failure: Failure) -> None:
        """Adds a new failure"""
        self.__failures.append(failure)

    def within(self, name: str) -> "Failures":
        """Adds outer label for all registered failures"""
        self.__failures = [failure.within(name) for failure in self.__failures]
        return self


AnyException = TypeVar("AnyException", bound=BaseException)


def _invalid(err_type: Type[AnyException], *args) -> AnyException:
    """Marks an error as a package validation error and returns it"""
    error = err_type(*args)
    setattr(error, "__validation_error__", True)
    return error


def _is_validation_error(error: Exception) -> bool:
    """Checks if the error is a package validation error"""
    return getattr(error, "__validation_error__", False)


NamePattern = re.compile(r'^(\w+(\[\w+]|\(\w+\))?)+([-.](\w+(\[\w+]|\(\w+\))?))*$')


def _validate_name(name: str) -> str:
    """Validates the name and returns it"""
    if not isinstance(name, str):
        raise _invalid(TypeError, "name must be a string")
    elif not NamePattern.match(name):
        raise _invalid(ValueError, f"invalid name: {name!r}")
    return name


FailureOrFailures = Union[Failure, Failures]
ExceptionTypeOrTypes = Union[Tuple[Type[Exception]], Type[Exception], None]


def _recursive_handler(handler: FailureHandler, failures: FailureOrFailures, ignore: ExceptionTypeOrTypes) -> None:
    """
    Handles the failures recursively with the given handler

    :param handler: A callable that takes two positional arguments (source: str, error: Exception)
    :param failures: Failures objects that holds all the error with their source label
    :param ignore: A tuple of exception types to ignore
    """
    if isinstance(failures, Failures):
        for failure in failures.failures:
            _recursive_handler(handler, failure, ignore)
    elif isinstance(failures, Failure):
        if ignore and isinstance(failures.error, ignore):
            return
        source, error = failures.source, failures.error
        if _is_validation_error(error):
            raise error
        handler(source, error)


class scope:
    __slots__ = "_name", "__subs", "_failures"

    _name: str
    __subs: Set[str]
    _failures: Optional[Failures]

    def __init__(self, name: str) -> None:
        """
        scope is a context manager object that capture errors and labels them
        then re-raises the wrapped failure to the higher context manager.

        :param name: the scope label (mandatory)
        """
        self._name = _validate_name(name)
        self.__subs = set()
        self._failures = None

    @property
    def name(self) -> str:
        return self._name

    def __enter__(self) -> "scope":
        return self

    @overload
    def add_failure(self, error: Exception, /, label: str) -> None:
        """Adds a labeled error to the failures scope"""

    @overload
    def add_failure(self, failure: Failure, /, label: Optional[str] = ...) -> None:
        """Adds a predefined failure to the failures scope with or without label"""

    def add_failure(self, error: Exception, /, label: Optional[str] = None) -> None:
        if isinstance(error, Failure):
            failure = error
            if label:
                failure.within(label)
        elif isinstance(error, Exception):
            if not label:
                raise _invalid(ValueError, "The error must be labeled")
            failure = Failure(label, error)
        else:
            raise _invalid(TypeError, f"Invalid error type {{{type(error).__name__}}}")
        if self._failures is None:
            self._failures = Failures(failure)
        else:
            self._failures.add(failure)

    def __exit__(self, _err_type, error, _err_tb) -> bool:
        if error is None and self._failures is None:
            return True
        if self._failures:
            self._failures.within(self._name)
        if isinstance(error, Exception):
            self.add_failure(error, self._name)
        elif isinstance(error, BaseException):
            return False
        raise cast(Failures, self._failures) from None

    def __call__(self, name: str) -> "scope":
        if name in self.__subs:
            raise _invalid(ValueError, f"The name {name!r} is already used in this scope")
        sub = SubScope(name, self)
        self.__subs.add(sub.name)
        return sub


class SubScope(scope):
    __slots__ = "_root",

    _root: scope

    def __init__(self, name: str, root: scope):
        super().__init__(name)
        self._root = root

    def __exit__(self, _err_type, error, _err_tb) -> bool:
        try:
            return super().__exit__(_err_type, error, _err_tb)
        except Failure as failure:
            self._root.add_failure(cast(Failures, failure))
            return True


class handle:
    __slots__ = ("__scope", "__handler", "__ignore")

    __scope: scope
    __handler: FailureHandler
    __ignore: ExceptionTypeOrTypes

    def __init__(
            self, name: str, handler: FailureHandler = default_handler, *, ignore: ExceptionTypeOrTypes = None
    ) -> None:
        if not (handler is None or callable(handler)):
            raise TypeError("Failure handler must be a callable")
        self.__scope = scope(name)
        self.__handler = handler
        self.__ignore = ignore

    def __enter__(self) -> scope:
        return self.__scope.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.__scope.__exit__(exc_type, exc_val, exc_tb)
        except Failure as failure:
            if self.__handler is None:
                return False
            _recursive_handler(self.__handler, failure, self.__ignore)
            return True
