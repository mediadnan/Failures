from typing import Optional, List, Set, Generator, Union, Type, Tuple

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


class DuplicateNameError(ValueError):
    """signals that a name have been defined twice"""


def _validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError(f"name must be a {str} instance")
    elif not name.isidentifier():
        raise ValueError(f"invalid name: {name}")
    return name


Failure_or_failures = Union[Failure, Failures]
Exception_type_or_types = Union[Tuple[Type[Exception]], Type[Exception], None]


def _recursive_handler(handler: FailureHandler, failures: Failure_or_failures, ignore: Tuple[Type[Exception]]) -> None:
    if isinstance(failures, Failures):
        for failure in failures.failures:
            _recursive_handler(handler, failure, ignore)
    elif isinstance(failures, Failure) and not (ignore and isinstance(failures.error, ignore)):
        handler(failures.source, failures.error)


class scope:
    __slots__ = ("__name", "__subs", "__sup_failures", "__sub_failures")

    __name: str
    __subs: Set[str]
    __sup_failures: Optional[List[Failure]]
    __sub_failures: List[Failure]

    def __init__(self, name: str, *, _failures: Optional[List[Failure]] = None) -> None:
        self.__name = _validate_name(name)
        self.__subs = set()
        self.__sup_failures = _failures
        self.__sub_failures = []

    @property
    def name(self) -> str:
        return self.__name

    def __enter__(self) -> "scope":
        return self

    def __exit__(self, failure_type, failure, traceback) -> bool:
        sub_failures = self.__sub_failures
        if not (failure or sub_failures):
            return True
        elif isinstance(failure, Failure):
            failure = failure.within(self.__name)
        elif isinstance(failure, Exception):
            failure = Failure(self.__name, failure)
        elif isinstance(failure, BaseException):
            return False
        if sub_failures:
            failures = Failures(*sub_failures).within(self.__name)
            failures.add(failure)
            failure = failures
        if self.__sup_failures is None:
            raise failure from None
        self.__sup_failures.append(failure)
        return True

    def __call__(self, name: str) -> "scope":
        if name in self.__subs:
            raise DuplicateNameError(f"The name {name!r} has already been given to a previous child of {self.__name!r}")
        sub = scope(name, _failures=self.__sub_failures)
        self.__subs.add(sub.name)
        return sub


class handle:
    __slots__ = ("__scope", "__handler", "__ignore")

    __scope: scope
    __handler: FailureHandler
    __ignore: Exception_type_or_types

    def __init__(
        self, name: str, handler: FailureHandler = print_failure, *, ignore: Exception_type_or_types = None
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
