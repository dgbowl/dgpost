import shutil
import os
import pytest


@pytest.fixture
def datadir(tmpdir, request):
    """
    from: https://stackoverflow.com/a/29631801
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)
    if os.path.isdir(test_dir):
        shutil.copytree(test_dir, str(tmpdir), dirs_exist_ok=True)
    base_dir, _ = os.path.split(test_dir)
    common_dir = os.path.join(base_dir, "common")
    if os.path.isdir(common_dir):
        shutil.copytree(common_dir, str(tmpdir), dirs_exist_ok=True)
    print(f"{tmpdir=}")
    return tmpdir
