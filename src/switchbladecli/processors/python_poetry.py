from pathlib import Path
import click
import shutil
import subprocess  # nosec

from tomlkit import dumps, loads

from switchbladecli.cli.bundle_cache import Bundle, BundleCache
from switchbladecli.cli.config import get_switchblade_config


class PythonPoetry:

    project_type = "python-poetry"

    def __init__(self, config: dict, verbose: bool):
        self._config = config
        self._project_folder = Path(config["project_dir"])
        self._verbose = verbose
        self._cache = BundleCache(self._config)


    # TODO: Make this an override
    def install_dev_tools(self, bundle: Bundle):
        # Read pyproject.toml and remove the sections [tool.poetry.group.switchblade]
        # and [tool.poetry.group.switchblade.dependencies], and add the ones from the
        # bundle.toml file in the commit SHA folder
        self._pyproject_file = self._project_folder / "pyproject.toml"
        self._poetry_lockfile = self._project_folder / "poetry.lock"

        self._pyproject_file_raw_before = self._pyproject_file.read_text(encoding="utf-8")
        self._poetry_lockfile_raw_before = self._poetry_lockfile.read_text(encoding="utf-8")  # TODO: handle missing file
        pyproject_config = loads(self._pyproject_file_raw_before)
        pyproject_config["tool"]["poetry"]["group"][
            "switchblade"
        ] = bundle.bundle_config["tool"]["poetry"]["group"]["switchblade"]
        # pyproject_config["tool"]["poetry"]["group"]["switchblade"][
        #     "dependencies"
        # ] = bundle.bundle_config["tool"]["poetry"]["group"]["switchblade"][
        #     "dependencies"
        # ]
        # Also take all other sections beginning with 'tool.' and add them to the pyproject.toml
        # unless there is already a section with the same name in the pyproject.toml
        for section in bundle.bundle_config["tool"]:
            if not section.startswith("poetry") and section not in pyproject_config["tool"]:
                pyproject_config["tool"][section] = bundle.bundle_config["tool"][
                    section
                ]
        with open(self._pyproject_file, "w") as pyproject_toml:
            pyproject_toml.write(dumps(pyproject_config))

        subprocess.run(
            ["poetry", "update", "--only", "switchblade"],
            cwd=self._project_folder,
            check=True,
            capture_output=False,
        )

    # TODO: Place this in a superclass
    def configure_dev_tools(self, bundle: Bundle):
        # For each file in the bundle, check if the file exists in the project folder
        pushed_files = []
        for file in bundle.get_files():
            if (self._project_folder / file).exists():
                # If the file exists, skip it
                self._cache.log(f"SKIPPED {file}")
                continue
            else:
                # If the file doesn't exist, copy it from the commit SHA folder to the project folder
                shutil.copyfile(
                    bundle.bundle_folder / file,
                    self._project_folder / file
                )
                pushed_files.append(file)
                self._cache.log(f"PUSHED {file}")
        return pushed_files


    # TODO: Place this in a superclass
    def run_linters(self, bundle: Bundle):
        # For each linter configured in the bundle, parse the section
        # linters[linter] > command and invoke the command in the project folder with `poetry run`
        for linter in bundle.bundle_config["linters"]["all"]:
            print(f"⚔️ Switchblade running {linter}...")
            self.run_linter(bundle, linter)
            self._cache.log(f"RAN {linter}")


    # TODO: Make this an override
    def run_linter(self, bundle: Bundle, linter: str):
        linter_command = bundle.bundle_config["linters"][linter]["command"]
        linter_command_list = linter_command.split(" ")
        subprocess.run(
            ["poetry", "run", *linter_command_list], cwd=self._project_folder, check=True
        )


    # TODO: Make this an override
    def cleanup_post_lint(self, bundle: Bundle, pushed_files: list):
        # Restore the original pyproject.toml
        if self._pyproject_file_raw_before:
            with open(self._pyproject_file, "w") as pyproject_toml:
                pyproject_toml.write(self._pyproject_file_raw_before)
        # Restore the original poetry.lock
        if self._poetry_lockfile_raw_before:
            with open(self._poetry_lockfile, "w") as poetry_lock:
                poetry_lock.write(self._poetry_lockfile_raw_before)


    # TODO: Place this in a superclass
    def lint(self):
        # Instantiating a Bundle object will fetch the latest bundle from the source or cache
        latest_bundle = Bundle(self._config)

        bundle_config = latest_bundle.bundle_config
        bundle_project_type = bundle_config["bundle"]["project_type"]

        if bundle_project_type != self.project_type:
            click.echo(
                f"⚔️ The Switchblade bundle is for a project of type {bundle_project_type}, but this project is of type {self.project_type}.",
                err=True
            )
            raise click.Abort()

        self._cache.log(f"LINTING {latest_bundle.version}")

        pushed_files = []
        try:
            print("⚔️ Switchblade installing tools...")
            self.install_dev_tools(latest_bundle)

            print("⚔️ Switchblade configuring tools...")
            pushed_files = self.configure_dev_tools(latest_bundle)

            self.run_linters(latest_bundle)

        except Exception:
            self._cache.log(f"LINTING {latest_bundle.version} FAILED")
            click.echo("⚔️ Linting finished with errors. 😭", err=True)
            raise click.Abort()

        finally:
            print("⚔️ Switchblade cleaning up...")
            # Remove the files from the project folder that were added in Step 3
            for file in pushed_files:
                (self._project_folder / file).unlink()
                self._cache.log(f"POPPED {file}")

            self.cleanup_post_lint(latest_bundle, pushed_files)

        self._cache.log(f"LINTING {latest_bundle.version} SUCCEEDED")

        click.echo("⚔️ Linting finished successfully. 😎")
