"""This library provides tools to label and handle errors anywhere in your code easily"""
from .core import Reporter, Failure, FailureException
from .functions import scoped
from .handler import Handler, print_failure, Not

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

__version__ = '1.0.0'
