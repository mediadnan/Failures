<div id="readme_header" style="text-align: center">
<h1 style="color: #913946ff; font-family: Candara, sans-serif;">Failures</h1>
<p style="color: #bf6572; font-family: Candara, sans-serif; font-style: italic">Successfully dealing with failures</p>
<br/>
<a href="https://github.com/mediadnan/Failures/actions/workflows/tests.yml" target="_blank"><img src="https://github.com/mediadnan/Failures/actions/workflows/tests.yml/badge.svg" alt="Tests"/></a>
<a href="https://codecov.io/gh/mediadnan/Failures" target="_blank"><img src="https://codecov.io/gh/mediadnan/Failures/branch/main/graph/badge.svg?token=E58PJ3OFME" alt="CodeCov"/></a>
<a href="https://www.python.org/downloads/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/failures" alt="PyPI - Python Version"/></a>
<a href="https://failures.readthedocs.io/" target="_blank"><img alt="Read the Docs" src="https://img.shields.io/readthedocs/failures"></a>
<a href="https://en.wikipedia.org/wiki/MIT_License" target="_blank"><img src="https://img.shields.io/github/license/mediadnan/failures" alt="License"/></a>
<a href="https://github.com/mediadnan/Failures/issues" target="_blank"><img src="https://img.shields.io/github/issues/mediadnan/failures" alt="GitHub issues" /></a>
<a href="https://pypi.org/project/failures/" target="_blank"><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/failures"></a>
</div>

## What is failures
A simple library aiming to ease reporting and handling errors in applications,
specially those dealing with inconsistent data and can fail in different parts of the code.
Dealing with this kind of problem becomes tedious when trying to wrap multiple parts with ``try...except`` blocks
and handling each one in place, or can add extra work when trying to implement a failure handling system
for each different application.

A solution to that problem is labeling different parts of code with meaningful names, and gather all failures
to be reported and handled at the end of each function call (session, path operation, *or whatever ...*).

This library comes with those exact tools, objects that hold failures between functions,
utilities to handle failures with a possibility to filter and handle failures differently, utilities to run a function
in a safe context while reporting errors, uncoupled failure labeling, and so on...

## Installation
``failures`` is available at PyPI, and requires python 3.8 or higher,
to install the latest release, run the ``pip`` command:

```shell
pip install failures
```

### Note
``failures`` comes with a default handler that just logs reported failures to the standard output,
if you want those logs to be colored, you can install this library with ``colorama`` as optional
dependency by running

```shell
pip install "failures[colors]"
```

## Usage
.. TODO