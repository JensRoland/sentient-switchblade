import os
from pathlib import Path

import pytest
import shutil

from unittest.mock import MagicMock, Mock, patch

AWS_TEST_REGION = "eu-west-1"


def pytest_configure(config: pytest.Config) -> None:
    """Mocked AWS Credentials to prevent accidental side effects in the cloud."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["GITHUB_TOKEN"] = "testing"

@pytest.fixture
def project(tmp_path):
    # Setup
    # Copy the contents of tests/project to the temp folder
    test_project_dir = os.path.join(os.path.dirname(__file__), "files", "testproject")
    project_dir = tmp_path
    shutil.copytree(test_project_dir, project_dir, dirs_exist_ok=True)

    # Set the current working directory to the temp folder
    os.chdir(tmp_path)

    # Test
    project_dir = tmp_path.resolve()
    return project_dir

@pytest.fixture
def project_with_cached_bundle(tmp_path):
    # Setup
    # Copy the contents of tests/project to the temp folder
    test_project_dir = os.path.join(os.path.dirname(__file__), "files", "testproject")
    project_dir = tmp_path
    shutil.copytree(test_project_dir, project_dir, dirs_exist_ok=True)

    # Copy the folder in files/previous.switchblade-cache to the temp folder
    test_cache_dir = os.path.join(os.path.dirname(__file__), "files", "previous.switchblade-cache")
    cache_dir = os.path.join(project_dir, ".switchblade-cache")
    shutil.copytree(test_cache_dir, cache_dir, dirs_exist_ok=True)

    # Set the current working directory to the temp folder
    os.chdir(tmp_path)

    # Test
    project_dir = tmp_path.resolve()
    return project_dir


@pytest.fixture
def project_with_config_file_name(tmp_path, config_file_name):
    # Setup
    # Copy the contents of tests/project to the temp folder
    test_project_dir = os.path.join(os.path.dirname(__file__), "files", "testproject")
    project_dir = tmp_path
    shutil.copytree(test_project_dir, project_dir, dirs_exist_ok=True)
    # Rename the config file to the name specified by the config_file_name fixture
    os.rename(os.path.join(project_dir, ".switchblade"), os.path.join(project_dir, config_file_name))

    # Set the current working directory to the temp folder
    os.chdir(tmp_path)

    # Test
    project_dir = tmp_path.resolve()
    return project_dir, config_file_name

@pytest.fixture
def project_with_bad_config(tmp_path, bad_config_file):
    # Setup
    # Copy the contents of tests/project to the temp folder
    test_project_dir = os.path.join(os.path.dirname(__file__), "files", "testproject")
    project_dir = tmp_path
    shutil.copytree(test_project_dir, project_dir, dirs_exist_ok=True)

    # Copy and overwrite the config file with the bad config file
    if bad_config_file:
        bad_config_file = os.path.join(os.path.dirname(__file__), "files", bad_config_file)
        shutil.copyfile(bad_config_file, os.path.join(project_dir, ".switchblade"))
    else:
        # If no config file is specified, delete the config file instead
        os.remove(os.path.join(project_dir, ".switchblade"))

    # Set the current working directory to the temp folder
    os.chdir(tmp_path)

    # Test
    project_dir = tmp_path.resolve()
    return project_dir


# Patch pygithub
@pytest.fixture()
def patched_pygithub():

    class GithubAsset:
        def __init__(self, name, decoded_content):
            self.name = name
            self.decoded_content = decoded_content

    # Read /tests/files/testbundle and list files
    bundle_folder = Path(os.path.join(os.path.dirname(__file__), "files", "testbundle"))
    bundle_files = [
        GithubAsset(str(file.relative_to(bundle_folder)), file.read_bytes())
        for file in bundle_folder.iterdir()
    ]
    with patch("switchbladecli.cli.bundle_cache.Github") as pygithub:
        pygithub.return_value.get_repo.return_value.get_branch.return_value.commit.sha = "12345678"
        pygithub.return_value.get_repo.return_value.get_contents.return_value = bundle_files
        yield pygithub


@pytest.fixture()
def patched_pygithub_with_exception():
    with patch("switchbladecli.cli.bundle_cache.Github") as pygithub:
        # Raise an exception when trying to get the repo
        pygithub.return_value.get_repo.side_effect = Exception("Test exception")
        yield pygithub
