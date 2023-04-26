import click

from switchbladecli.modes.python_poetry import PythonPoetry
from switchbladecli.cli.config import get_switchblade_config


@click.command()
@click.pass_context
def test(ctx):
    project_dir = ctx.obj["project_dir"]
    config_file = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    test_command(verbose, project_dir, config_file)


def test_command(verbose: bool, project_dir: str, config_file: str):
    config = get_switchblade_config(verbose, project_dir, config_file)

    mode = config["switchblade"]["mode"]

    tool_runner = None
    if mode == "python-poetry":
        tool_runner = PythonPoetry(config, verbose)
    else:
        raise click.ClickException(
            f"Project mode {mode} is not supported by Switchblade."
        )

    tool_runner.test()
