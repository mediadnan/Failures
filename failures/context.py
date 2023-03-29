from contextlib import contextmanager
from typing import Optional, List, Dict, Set

from .handler import FailureHandler, Failure, print_failure


def _validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError(f"name must be a {str} instance")
    elif not name.isidentifier():
        raise ValueError(f"invalid name: {name}")
    return name


class DuplicateNameError(ValueError):
    """signals that a name have been defined twice"""


class Reporter:
    __slots__ = ("__name", "__subs", "__sub_failures")

    __name: str
    __subs: Set[str]
    __sub_failures: Optional[Dict[str, Failure]]

    def __init__(self, name: str, _failures: Optional[Dict[str, Failure]] = None) -> None:
        self.__name = _validate_name(name)
        self.__subs = set()
        self.__sub_failures = _failures

    @property
    def name(self) -> str:
        return self.__name

    def __enter__(self) -> "Reporter":
        return self

    def __exit__(self, error_type, error, traceback):
        raise NotImplementedError

    def __call__(self, name: str) -> "Reporter":
        if name in self.__subs:
            raise DuplicateNameError(f"The name {name!r} has already been given to a previous child of {self.__name!r}")
        if self.__sub_failures is None:
            self.__sub_failures = dict()
        sub = Reporter(name, self.__sub_failures)
        self.__subs.add(sub.name)
        return sub


@contextmanager
def scope(name: str):
    _validate_name(name)
    try:
        yield
    except Failure as failure:
        raise failure.within(name)
    except Exception as error:
        raise Failure(name, error)


@contextmanager
def handle(name: str, handler: Optional[FailureHandler] = print_failure):
    _validate_name(name)
    try:
        yield
    except Failure as failure:
        failure = failure.within(name)
        handler and handler(failure.source, failure.error)
    except Exception as error:
        handler and handler(name, error)
