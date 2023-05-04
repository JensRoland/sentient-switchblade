import click

from operator import itemgetter
from switchbladecli.modes.tool_runner import get_tool_runner


@click.command()
@click.argument("linter", required=False)
@click.pass_context
def lint(ctx, linter: str):
    """Run linter(s) on project.
    
    LINTER: Linter to run. If not specified, all linters will be run.
    """
    project_dir, config, verbose = itemgetter("project_dir", "config", "verbose")(ctx.obj)
    cmd_lint(verbose, project_dir, config, linter)


def cmd_lint(verbose: bool, project_dir: str, config: dict, linter_tool: str = "all"):
    tool_runner = get_tool_runner(config)(config, verbose)
    tool_runner.lint(linter_tool)
