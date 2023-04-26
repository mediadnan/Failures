# Failures
_labeling failures for humans_

## Introduction
In most applications that interact with data (_specially inconsistent data_) failures are one thing to expect,
and more so in dynamically typed languages like python.
A failure may happen when trying to access a dictionary key that doesn't exist in a specific case, 
or trying to perform string operations on a returned function value that has returned ``None`` instead,
and many more other failures to expect.

As a default behavior, the interpreter raises a specific ``Exception`` to stop the process and avoid further lower level
bugs and issues, giving us traceback information about where that error happened and why it happened.

However, in production environments, we rarely want our application to crash for every failure that occurs, 
and we want it to be more robust against expected and unexpected failures. But in the other hand, silencing 
and ignoring all failures is not a desired behavior either, as it doesn't give us isight about what just happened.

The solution is to catch and handle each exception while performing an operation that might fail,
wrapping it with ``try-except`` in place to provide alternative code instead, together with logging,
this can be enough for smaller applications. It solves both problems avoiding crashes and reporting the issue
to let us know what happened.

But when the application starts to grow with multiple components and modules, wrapping each operation in ``try-except`` 
becomes tedious and repetitive, imagine wrapping many parts of the application with ``try-except`` blocks and
handling inplace each exception with almost the same logic ``print('... has failed while ...')`` and then some
alternative code, just to decide later to switch to ``logger.error('... has failed while ...')`` or another alternative,
that will require us to go and refactor multiple parts of the code.
A better solution is to separate the failure handling logic in a single place and call a specific
handling mechanism in the appropriate situation, this way we can avoid writing the same logic multiple times.

Besides that, bigger apps contain reusable decoupled components, components that can be used by other components,
and often they do not know the context where they're being used or which component is using them,
util we inspect the traceback frames in case of failures to generate better reports ``logger.error(..., exc_info=...)``,
this will improve the reports together with exception information.

This approach almost solves our problem of handling failures, but implementing a similar handling mechanism
across apps can also become repetitive, and default error tracebacks are more **file and line number** oriented,
it would be easier to also pinpoint the failure by its logical location like ``users.login.email_parsing``
and ``users.registration.email_parsing``, that would be more readable for us when reading logs and reports.

This library it's a solution to deal with application failures efficiently, it provides tools to both report and handle
different failures easily reducing boilerplate code needed to do it supporting both simple and complex use-cases.

This documentation will serve both as tutorial and reference to use this library, containing use-case
examples and resource definitions, it splits dealing with failures in two phases; 

1. Capturing, labeling and reporting failures,
2. Handling the captured failures with the appropriate function. 

The first chapter will discuss in details different ways to label and report failures, the second one will go in details
about how to handle the reported failures.

## Installation
``failures`` is available for python 3.8 or newer, to be able to use it, 
it must be installed in your environment from PyPI using the pip command.

````shell
pip install failures
````

````{toctree}
    :hidden:
    :caption: User Guide
    :maxdepth: 2
guide/reporter
guide/scopes
guide/handler
````
````{toctree}
    :maxdepth: 2
    :hidden:
    :caption: API Reference
api_ref
````
````{toctree}
    :maxdepth: 1
    :hidden:
    :caption: About
versions
license
````
