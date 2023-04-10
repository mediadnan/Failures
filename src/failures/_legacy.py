from typing import Union, Optional, Type

from ._print import print_failure
from .core import Scope, FailureHandler, FailureFilters, _invalid, scope, handler_, deprecated


__all__ = ('handle', 'SubScope')


@deprecated("failures.handle will be removed in failures 1.0, use failures.scope with handler instead.")
class handle:
    __slots__ = ('__scope',)
    __scope: Scope

    def __init__(
            self,
            name: str,
            handler: Optional[FailureHandler] = print_failure, *,
            ignore: Union[FailureFilters, Type[Exception]] = None,
    ) -> None:
        if callable(handler):
            _handler = handler_(handler, ignore=(ignore or ()))
        elif handler is None:
            _handler = None
        else:
            raise _invalid(TypeError, "Failure handler must be a callable")
        self.__scope = scope(name, _handler)

    def __enter__(self) -> Scope:
        return self.__scope.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.__scope.__exit__(exc_type, exc_val, exc_tb)


@deprecated("SubScope is considered internal api and will be removed in failures 1.0")
class SubScope(Scope):
    pass
