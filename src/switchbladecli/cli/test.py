import click

from switchbladecli.modes.python_poetry import PythonPoetry
from switchbladecli.cli.config import get_switchblade_config


@click.command()
@click.argument("test", required=False)
@click.pass_context
def test(ctx, test: str):
    """Run testing tool(s) on project.
    
    TEST: Testing tool to run. If not specified, all testing tools will be run.
    """
    project_dir = ctx.obj["project_dir"]
    config_file = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    test_command(verbose, project_dir, config_file, test)


def test_command(verbose: bool, project_dir: str, config_file: str, test_tool: str = "all"):
    config = get_switchblade_config(verbose, project_dir, config_file)

    if test_tool is None:
        test_tool = "all"

    mode = config["switchblade"]["mode"]

    tool_runner = None
    if mode == "python-poetry":
        tool_runner = PythonPoetry(config, verbose)
    else:
        raise click.ClickException(
            f"Invalid project mode {mode} specified."
        )

    tool_runner.test(test_tool)
