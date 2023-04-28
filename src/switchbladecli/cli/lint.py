import click

from switchbladecli.modes.python_poetry import PythonPoetry
from switchbladecli.cli.config import get_switchblade_config


@click.command()
@click.argument("linter", required=False)
@click.pass_context
def lint(ctx, linter: str):
    """Run linter(s) on project.
    
    LINTER: Linter to run. If not specified, all linters will be run.
    """
    project_dir = ctx.obj["project_dir"]
    config_file = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    lint_command(verbose, project_dir, config_file, linter)


def lint_command(verbose: bool, project_dir: str, config_file: str, linter_tool: str = "all"):
    config = get_switchblade_config(verbose, project_dir, config_file)

    if linter_tool is None:
        linter_tool = "all"

    mode = config["switchblade"]["mode"]

    tool_runner = None
    if mode == "python-poetry":
        tool_runner = PythonPoetry(config, verbose)
    else:
        raise click.ClickException(
            f"Invalid project mode {mode} specified."
        )

    tool_runner.lint(linter_tool)
