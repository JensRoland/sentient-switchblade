import click

from operator import itemgetter
from switchbladecli.modes.tool_runner import get_tool_runner


@click.command()
@click.argument("test", required=False)
@click.pass_context
def test(ctx, test: str):
    """Run testing tool(s) on project.
    
    TEST: Testing tool to run. If not specified, all testing tools will be run.
    """
    project_dir, config, verbose = itemgetter("project_dir", "config", "verbose")(ctx.obj)
    result = cmd_test(verbose, project_dir, config, test)
    if not result:
        ctx.exit(1)


def cmd_test(verbose: bool, project_dir: str, config: dict, test_tool: str = "all"):
    tool_runner = get_tool_runner(config)(config, verbose)
    return tool_runner.test(test_tool)
