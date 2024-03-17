import os
from shutil import rmtree
import pytest
from main import init, output_dir, build_folder_prefix, flavors

test_folder_name = "test"
test_folder_path = os.path.join(output_dir, test_folder_name)


@pytest.fixture(autouse=True)
def run_after_tests():
    if os.path.exists(test_folder_path):
        rmtree(test_folder_path)


@pytest.fixture(scope="session", autouse=True)
def run_around_tests():
    yield
    if os.path.exists(test_folder_path):
        rmtree(test_folder_path)


def test_create_all_dependencies():
    init(test_folder_name, [])


def test_unavailable_flavor():
    argv = ["--group", "noml", "--flavor", "cuda"]

    with pytest.raises(Exception):
        init(test_folder_name, argv)


def test_missing_argument():
    argv = ["--group", "noml"]

    with pytest.raises(Exception):
        init(test_folder_name, argv)


def test_check_folder():
    argv = []
    for group in flavors:
        for flavor in group["flavors"]:
            argv = ["--group", group["name"], "--flavor", flavor["name"]]
            folder = build_folder_prefix + group["name"] + "/" + flavor["name"]
            init(test_folder_name, argv)
            flavor_path = os.path.join(test_folder_path, folder)
            assert os.path.exists(flavor_path) is True
