"""Failures package provides tools to label and track errors anywhere in your code easily"""
from ._print import print_failure
from .core import handler_ as handler, scope, scoped, FailureHandler, Failure
from ._legacy import handle, SubScope   # deprecated API


# -------------------------------- WARNING --------------------------------- #
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


__version__ = '0.2.0'
