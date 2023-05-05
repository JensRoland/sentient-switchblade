from switchbladecli.cli.config import find_config_file, get_switchblade_config
from switchbladecli.cli.test import cmd_test


def test_test_all(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    test_result = cmd_test(False, project, config)

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pytest", "-c", "pyproject.toml", fp.any()]) == 1

    assert test_result == True


def test_test_one(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    cmd_test(False, project, config, "pytest")

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pytest", "-c", "pyproject.toml", fp.any()]) == 1


def test_test_all_with_errors(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    # Mock the pytest command to return a non-zero exit code
    fp.register(["poetry", "run", "pytest", "-c", "pyproject.toml", fp.any()], returncode=1)
    # Mock all other poetry commands
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    test_result = cmd_test(False, project, config)

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pytest", "-c", "pyproject.toml", fp.any()]) == 1

    assert test_result == False
