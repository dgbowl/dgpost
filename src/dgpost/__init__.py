import sys
from importlib.metadata import version
from .main import run_with_arguments

__all__ = ["run_with_arguments"]
__version__ = version("dgpost")

sys.path += sys.modules["dgpost"].__path__



