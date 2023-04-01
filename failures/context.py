from typing import Optional, List, Set, Generator, Union, Type, Tuple, overload, TypeVar

from .handler import FailureHandler, print_failure


class Failure(Exception):
    def __init__(self, source: str, error: Exception):
        self.source: str = source
        self.error: Exception = error

    def within(self, name: str) -> "Failure":
        self.source = name + "." + self.source
        return self


class Failures(Failure):
    def __init__(self, *failures: Failure) -> None:
        self.__failures: List[Failure] = list(failures)

    @property
    def failures(self) -> Generator[Failure, None, None]:
        yield from self.__failures

    def add(self, failure: Failure) -> None:
        self.__failures.append(failure)

    def within(self, name: str) -> "Failures":
        self.__failures = [failure.within(name) for failure in self.__failures]
        return self


AnyException = TypeVar("AnyException", bound=BaseException)


def _invalid(err_type: Type[AnyException], *args) -> AnyException:
    error = err_type(*args)
    setattr(error, "__validation_error__", True)
    return error


def _is_validation_error(error: Exception) -> bool:
    return getattr(error, "__validation_error__", False)


def _validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise _invalid(TypeError, "name must be a string")
    elif not name.isidentifier():
        raise _invalid(ValueError, f"invalid name: {name!r}")
    return name


FailureOrFailures = Union[Failure, Failures]
ExceptionTypeOrTypes = Union[Tuple[Type[Exception]], Type[Exception], None]


def _recursive_handler(handler: FailureHandler, failures: FailureOrFailures, ignore: Tuple[Type[Exception]]) -> None:
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
    __slots__ = ("_name", "__subs", "_failures", "_root")

    _name: str
    __subs: Set[str]
    _failures: Optional[Failures]
    _root: Optional["scope"]

    def __init__(self, name: str, *, root: Optional["scope"] = None) -> None:
        self._name = _validate_name(name)
        self.__subs = set()
        self._root = root
        self._failures = None

    @property
    def name(self) -> str:
        return self._name

    def __enter__(self) -> "scope":
        return self

    @overload
    def add_failure(self, error: Exception, /, label: str) -> None:
        ...

    @overload
    def add_failure(self, failure: Failure, /, label: Optional[str] = ...) -> None:
        ...

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
        if self._root is None:
            raise self._failures from None
        self._root.add_failure(self._failures)
        return True

    def __call__(self, name: str) -> "scope":
        if name in self.__subs:
            raise _invalid(ValueError, f"The name {name!r} is already used in this scope")
        sub = scope(name, root=self)
        self.__subs.add(sub.name)
        return sub


class handle:
    __slots__ = ("__scope", "__handler", "__ignore")

    __scope: scope
    __handler: FailureHandler
    __ignore: ExceptionTypeOrTypes

    def __init__(
            self, name: str, handler: FailureHandler = print_failure, *, ignore: ExceptionTypeOrTypes = None
    ) -> None:
        if not callable(handler):
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
            _recursive_handler(self.__handler, failure, self.__ignore)
            return True
