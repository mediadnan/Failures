# Failures
_labeling failures for humans_

## Introduction
When interacting with data, _either user input or raw inconsistent api data_, errors are surely one thing to expect,
and it becomes painful to maintain and monitor those errors as projects grow, especially when having multiple independent
components that interact with each-other, so when a component fails, following tracebacks doesn't always give us
an instantaneous picture about that failure.

Failure comes with tools to tag _(label)_ with meaningful names code areas that might fail, so when a failure occurs
in a nested component while processing some data, ``failures`` concatenates those labels from outer to inner and reports
the actual error together with the source name _(which looks something like ``outer_tag.middle_tag.inner_tag``)_

This documentation will cover each tool that ``failures`` provides, together with comprehensive examples and use-cases.


## Installation
``failures`` is available for python 3.8 or newer and can be installed
from PyPI using the pip command

````shell
pip install failures
````


````{toctree}
    :maxdepth: 2
    :hidden:
    :caption: User Guide

guide/scopes
````
````{toctree}
    :maxdepth: 1
    :hidden:
    :caption: About

versions
````
