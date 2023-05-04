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
This library simplifies dealing with application failures especially when using multiple nested components
that process some data and could fail at any point.

Often in production, the app must be robust enough against errors but still report them so we can improve it regularly,
this requires us as developers to isolate those operations _(usually within ``try...except`` blocks)_ then catch
any possible errors to report them and provide an alternative result _(like returning ``None``)_.
This is an additional job to be done to keep achieve the production robustness.

Meanwhile, this library suggests some tools to ease this process and divides it into two main phases, 
the first is capturing failures through an application action and between function calls while giving them
meaningful labels and optionally explicit metadata to help us understand them later and their context,
the second phase is to process those collected failures with the ability to filter and choose different
handling action for different type of failures.

The library focuses on two main factors, simplicity and performance, by keeping the syntax easy, clean and intuitive
for a better and more readable code, and by optimizing its code to minimize the impact on your application.

## Installation
``failures`` is available at PyPI, it requires python 3.8 or higher, to install it run the ``pip`` command:

```shell
pip install failures
```

## Usage
This example will show the tip of the iceberg, for a more complete tutorial refer to the documentation
page at [documentation page](https://failures.readthedocs.org).

````python
from failures import Reporter, Handler

# TODO: example
````

