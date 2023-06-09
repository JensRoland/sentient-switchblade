from switchbladecli.cli.config import find_config_file, get_switchblade_config
from switchbladecli.cli.lint import cmd_lint


def test_lint_all(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    lint_result = cmd_lint(False, project, config)

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pylint", "src"]) == 1
    assert fp.call_count(["poetry", "run", "pre-commit", "run", "--all-files"]) == 1

    assert lint_result == True


def test_lint_one(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    cmd_lint(False, project, config, "pylint")

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pylint", "src"]) == 1
    assert fp.call_count(["poetry", "run", "pre-commit", "run", "--all-files"]) == 0


def test_lint_all_with_errors(fp, project, patched_pygithub):
    fp.keep_last_process(True)
    # Mock the pylint command to return a non-zero exit code
    fp.register(["poetry", "run", "pylint", "src"], returncode=1)
    # Mock all other poetry commands
    fp.register(["poetry", fp.any()])

    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)

    lint_result = cmd_lint(False, project, config)

    assert fp.call_count(["poetry", "update", "--only", "switchblade"]) == 1
    assert fp.call_count(["poetry", "run", "pylint", "src"]) == 1
    assert fp.call_count(["poetry", "run", "pre-commit", "run", "--all-files"]) == 1

    assert lint_result == False
