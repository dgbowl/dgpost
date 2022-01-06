import sys

sys.path += sys.modules["dgpost"].__path__

from .main import run_with_arguments, run
