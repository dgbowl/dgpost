import sys
from importlib.metadata import version
from .main import run_with_arguments, run

__all__ = ["run_with_arguments", "run"]
__version__ = version("dgpost")

sys.path += sys.modules["dgpost"].__path__
