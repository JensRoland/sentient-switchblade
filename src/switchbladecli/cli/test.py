import click

from switchbladecli.modes.python_poetry import PythonPoetry


@click.command()
@click.argument("test", required=False)
@click.pass_context
def test(ctx, test: str):
    """Run testing tool(s) on project.
    
    TEST: Testing tool to run. If not specified, all testing tools will be run.
    """
    project_dir = ctx.obj["project_dir"]
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    test_command(verbose, project_dir, config, test)


def test_command(verbose: bool, project_dir: str, config: dict, test_tool: str = "all"):
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
