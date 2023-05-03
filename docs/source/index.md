# [Failures]{#title}
[_Successfully dealing with failures_]{#sub-title}

## Introduction
In most applications that interact with data (_inconsistent data in particular_) failures are one thing to expect,
and more so in loosely typed languages like python.
A failure may happen when trying to access a dictionary key that doesn't exist in a specific case, 
or trying to perform string operations on a returned function value that has returned ``None`` instead,
and many more other failures to expect.

As a default behavior, the interpreter raises a specific ``Exception`` to stop the process and avoid further lower level
bugs and issues, giving us traceback information about where that error happened and why it happened.

However, in production environments, we rarely want our application to crash for every failure that occurs, 
and we want it to be more robust against expected and unexpected failures.
But on the other hand, silencing and ignoring all the failures is not a desired behavior either, 
as it doesn't give us insight about what is happening in our application.

The solution is to catch and handle each exception when performing an operation that might fail,
wrapping it within ``try-except`` block to catch and log that failure while providing and alternative result 
in that case, and this can be enough for smaller applications.
It solves both problems; avoiding crashes and reporting the issue to let us know what happened.

But when the application starts to grow with multiple components and modules, wrapping each operation in ``try-except`` 
becomes tedious and repetitive, imagine wrapping many parts of the application with ``try-except`` blocks and
handling inplace each exception with almost the same logic ``print('... has failed while ...')`` and then some
alternative code, just to decide later to switch to ``logger.error('... has failed while ...')`` or another alternative,
that will require us to go and refactor multiple parts of the code.
A better solution is to separate the failure handling logic in a single place and call a specific
handling mechanism in the appropriate situation, this way we can avoid writing the same logic multiple times.

Besides that, bigger apps contain reusable decoupled components, components that can be used by other components,
and often they do not know the context where they're being used or which component is using them,
unless we inspect the traceback frames in case of an error to generate better reports ``logger.error(..., exc_info=...)``,
this will improve the reports together with exception information.

This approach almost solves our problem of handling failures, but implementing a similar handling mechanism
across apps can also become repetitive, and default error tracebacks are more **file and line number** oriented,
it would be easier to also pinpoint the failure by its logical location like ``users.login.email_parsing``
and ``users.registration.email_parsing``, that would be more readable for us when reading logs and reports.

So that problem is what ``failures`` is trying to efficiently solve, it provides tools to both report and handle
different failures easily reducing boilerplate code needed to do it, supporting both simple and complex use-cases.

This document will serve both as tutorials for new users and reference to look into when using this library, 
it will be divided into two main chapters;

1. [Reporting failures](#reporting): Explains how to capture, label and gather failures,
2. [Handling failures](#handling): Explains how to handle the collected failures. 

Reporting and handling failures is done many times throughout the application's lifecycle, to be specific; 
it is triggered each time an action is called.
So in the context of a web app, for example, the failure reporting lifecycle must start when the app receives a request
from the client until it sends the response back; the failure handling should be either just before or after sending 
the response, some should be handled before to give that client a descriptive response, others
can be processed after for analytics and monitoring.

## Installation
``failures`` is available for python 3.8 or newer, to be able to use it, 
it must be installed in your environment from PyPI using the pip command.

````shell
pip install failures
````

If ``colorama`` is installed in your environment, the default handler will print failures highlighted with colors; 
otherwise, it will print them normally.

To install failures together with ``colorama``, we can install it using this command ``pip install "failures[colors]"``

## Bug report
If you encounter any bug or issue using this library, or even want to contribute by giving us new suggestions;
you can open an issue in the official [GitHub ``failures`` repository](https://github.com/mediadnan/Failures/issues). 

````{toctree}
    :hidden:
    :caption: User Guide
    :maxdepth: 3
guide/reporting
guide/handling
guide/conclusion
````
````{toctree}
    :hidden:
    :maxdepth: 2
    :caption: API Reference
api_ref
````
````{toctree}
    :hidden:
    :maxdepth: 1
    :caption: About
versions
license
````
