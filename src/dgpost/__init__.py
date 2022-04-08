import sys

sys.path += sys.modules["dgpost"].__path__

from .main import run_with_arguments, run

from . import _version
__version__ = _version.get_versions()['version']
