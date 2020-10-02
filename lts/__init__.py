#
# **pkgutil-style namespace packages**
#
#Python 2.3 introduced the pkgutil module and the extend_path function. 
#This can be used to declare namespace packages that need to be compatible with both Python 2.3+ and Python 3. 
#This is the recommended approach for the highest level of compatibility.
#
#To create a pkgutil-style namespace package, you need to provide an __init__.py file for the namespace package:
#
#  setup.py
#  mynamespace/
#      __init__.py  # Namespace package __init__.py
#      subpackage_a/
#          __init__.py  # Sub-package __init__.py
#          module.py
#
#The __init__.py file for the namespace package needs to contain only the following:
#
__path__ = __import__('pkgutil').extend_path(__path__, __name__)
#
#
# for import *:
#
__all__ = ["emb_text_seg", "uts", "pre_proc", "slts_corpus"]
#
__version__ = (0, 0, 2)
#
from .uts.c99 import C99
from .uts.texttiling import TextTiling