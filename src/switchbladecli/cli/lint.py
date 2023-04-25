import click

from switchbladecli.processors.python_poetry import PythonPoetry
from switchbladecli.cli.config import get_switchblade_config


@click.command()
@click.pass_context
def lint(ctx):
    project_dir = ctx.obj["project_dir"]
    config_file = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    lint_command(verbose, project_dir, config_file)


def lint_command(verbose: bool, project_dir: str, config_file: str):
    config = get_switchblade_config(verbose, project_dir, config_file)

    project_type = config["switchblade"]["project_type"]

    processor = None
    if project_type == "python-poetry":
        processor = PythonPoetry(config, verbose)
    else:
        raise click.ClickException(
            f"Project type {project_type} is not supported by Switchblade."
        )

    processor.lint()
