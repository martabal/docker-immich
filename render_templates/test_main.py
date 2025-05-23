import os
from shutil import rmtree
import pytest
from .main import init, App

test_folder_name = "test"
test_folder_path = os.path.join(App.output_dir, test_folder_name)


@pytest.fixture(autouse=True)
def run_after_tests():
    if os.path.exists(test_folder_path):
        rmtree(test_folder_path)


@pytest.fixture(scope="session", autouse=True)
def run_around_tests():
    yield
    if os.path.exists(test_folder_path):
        rmtree(test_folder_path)


def test_count_dependencies():
    assert len(App.flavors) == 6


def test_create_all_dependencies():
    argv = ["--build-path", test_folder_name]
    init(argv)


def test_wrong_args():
    with pytest.raises(SystemExit) as e:
        argv = ["-n"]
        init(argv)
    assert e.type is SystemExit
    with pytest.raises(SystemExit) as e:
        argv = ["-n", "--flavor", App.flavors[0]["name"]]
        init(argv)
    assert e.type is SystemExit


def test_check_folder():
    for flavor in App.flavors:
        argv = ["--flavor", flavor["name"], "--build-path", test_folder_name]
        init(argv)
        folder = App.build_folder_prefix + flavor["name"]
        flavor_path = os.path.join(test_folder_path, folder)
        dockerfile_path = os.path.join(flavor_path, "Dockerfile")
        root_path = os.path.join(flavor_path, "root")
        assert os.path.exists(flavor_path) is True
        assert os.path.exists(dockerfile_path) is True
        assert os.path.exists(root_path) is True
