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

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

#
#

__version__ = (0, 0, 2)


#
# "import lts" will import the following classes but also the corresponding modules (.py files)
#
_names=[
            {'classname':'EmbeddingsTextSegmenter', 'basemodulename':'emb_text_seg', 'submodulename':''},
            {'classname':'SegmentedCorpus',         'basemodulename':'slts_corpus',  'submodulename':''},
            {'classname':'TextPreProcessor',        'basemodulename':'pre_proc',     'submodulename':''},
            {'classname':'C99',                     'basemodulename':'uts',          'submodulename':'.c99'},
            {'classname':'TextTiling',              'basemodulename':'uts',          'submodulename':'.texttiling'}
        ]

for _name in _names:
    exec(f'from .{_name["basemodulename"]}{_name["submodulename"]} import {_name["classname"]}')

#
# for import *:
#
#__all__ = list(set([_name['basemodulename'] for _name in _names] + [_name['classname'] for _name in _names]))
__all__ = list(set([_name['basemodulename'] for _name in _names] ))
#["uts", "texttiling", "emb_text_seg", "slts_corpus", "pre_proc", "SegmentedCorpus", "EmbeddingsTextSegmenter", "TextPreProcessor", "C99"]
