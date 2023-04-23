"""Failures package provides tools to label and track errors anywhere in your code easily"""
from .core import Reporter, scope, scoped, Failure, FailureException, Severity, OPTIONAL, NORMAL, REQUIRED
from .handler import handle, filtered, combine, print_failure

# -------------------------------- WARNING! -------------------------------- #
#                                                                            #
#       Anything that starts with an _ or not explicitly imported here       #
#       or mentioned anywhere in the documentation is considered             #
#       internal API and implementation details                              #
#       and could potentially change in minor/patch versions                 #
#       USING PRIVATE MEMBERS MAY POTENTIALLY BREAK                          #
#       YOUR APP IN ANY NEXT RELEASE,                                        #
#       and the package does not commit to keep the                          #
#       internal API compatibility for the next patch/minor version.         #
#                                                                            #
# -------------------------------------------------------------------------- #

__version__ = '1.0.0-dev'
