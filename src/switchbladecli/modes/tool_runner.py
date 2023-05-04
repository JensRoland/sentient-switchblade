from switchbladecli.exceptions import InvalidConfigValue
from switchbladecli.modes.python_poetry import PythonPoetry

def get_tool_runner(config):
    mode_map = {
        "python-poetry": PythonPoetry
    }
    if config["switchblade"]["mode"] not in mode_map:
        raise InvalidConfigValue(f'Invalid project mode {config["switchblade"]["mode"]} specified.')

    return mode_map[config["switchblade"]["mode"]]
