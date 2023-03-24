"""
failures module provides a utility class Reporter to help 
handling nested errors, this reporter derrives a new reporter
with a dot separated name, so a reporter with name 'root'
when called with name 'child', returns a new reporter with 
the name 'root.child'

failures (error/exceptions) are handled with three different severities: OPTIONAL, NORMAL and REQUIRED.

OPTIONAL
    Failures marked with OPTIONAL severity are basically ignored, this is 
    useful for processes that are expected to fail (inconsistend data)

NORMAL
    Failures marked with NORMAL severity are reported but the error itsel is 
    contained so and the main program don't crash

REQUIRED
    Failures marked with REQUIRED severity are reported and the error is reraised

the failures module comes with a default handler which logs failures using the 
the logging module, this handler is like a placeholder, a more custom 
failure handler should be implemented by the user.
"""
from enum import Enum
from datetime import datetime as DateTime
import logging
from typing import Any, Optional, Dict, Callable


__version__ = '0.1.0-alpha.1'
__all__ = ('Severity', 'OPTIONAL', 'NORMAL', 'REQUIRED', 'Failure', 'Reporter', '__version__')


class Severity(Enum):
    OPTIONAL = 0
    NORMAL = 1
    REQUIRED = 2


OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED

FailureHandler = Callable[[str, Exception, Severity, DateTime, Dict[str, Any]], None]


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.WARNING)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
stream_handler.setFormatter(logging.Formatter("%(failure_source)s [%(levelname)s] :: %(message)s (%(asctime)s)"))
LOGGER.addHandler(stream_handler)
del stream_handler


def log_failure(source: str, error: Exception, severity: Severity, datetime: DateTime, details: Dict[str, Any]) -> None:
    """Default failure handler"""
    LOGGER.error(str(error), exc_info=error, stack_info=2, extra={'failure_source': source})
    if severity is REQUIRED:
        raise error


class Reporter:
    __slots__ = '__name', '__severity', '__handler', '__root', '__details'
    
    def __init__(
            self,
            name: str,
            severity: Severity = NORMAL,
            handler: Optional[FailureHandler] = log_failure,
            **details
    ) -> None:
        """
        Reporter keeps track of the source for nested calls
        and calls the handler when an error occurs with rich
        information.
        
        :param name: The name of the reporter
        :param handler: the function to be called when failures occur
        :param severity: the level of severity (OPTIONAL, NORMAL, REQUIRED)
        :param details: any additional details to be reported
        """
        root = details.pop('__reporter_root__', None)
        assert isinstance(name, str) and name, "name must be a non-empty string"
        assert isinstance(severity, Severity), "severity must be of type Severity"
        assert callable(handler) or handler is None, "handler must be a callable that expects a dict"
        assert root is None or isinstance(root, Reporter), "__reporter_root__ must be instance of Reporter"
        self.__name: str = name
        self.__severity: str = severity
        self.__handler: Optional[FailureHandler] = handler
        self.__root: Optional[Reporter] = root
        self.__details: Dict[str, Any] = details

    def __call__(self, name: Optional[str] = None, severity: Severity = NORMAL, **details) -> 'Reporter':
        """Derives a new reporter with a hierarchical name from the current one"""
        return Reporter(name, self.handler, severity, __reporter_root__=self, **details)

    def __enter__(self) -> 'Reporter':
        """Reporter as a context will capture exceptions and report them"""
        return self
    
    def __exit__(self, _exc_type, exc_val, _exc_tb) -> bool:
        if exc_val is None:
            return True
        elif isinstance(exc_val, Exception):
            self.failure(exc_val)
            return True
        return False  # propagate higher exception types (like BaseException)


    @property
    def name(self) -> str:
        if self.__root is None:
            return self.__name
        return self.__root.name + '.' + self._name

    @property
    def details(self) -> Dict[str, Any]:
        if self.__root is None:
            return self.__details
        return {**self.__root.details, **self.__details}

    @property
    def severity(self) -> Severity:
        return self.__severity

    def report(self, failure: Exception) -> None:
        """Handles the failure"""
        datetime = DateTime.now()
        if (self.__severity is OPTIONAL) or (self.__handler is None):
            return
        self.__handler({
            'source': self.name,
            'error': failure,
            'severity': self.__severity,
            'datetime': datetime,
            'details': self.details,
        })
