from pathlib import Path
import click
import shutil
import subprocess  # nosec

from datetime import datetime, timezone
from mergedeep import merge
from tomlkit import dumps, loads

from switchbladecli.cli.bundle_cache import Bundle, BundleCache


class PythonPoetry:

    SKIP_UPDATE_IF_INSTALLED_WITHIN = 60*60*24  # 24 hours
    mode = "python-poetry"

    def __init__(self, config: dict, verbose: bool):
        self._config = config
        self._project_folder = Path(config["project_dir"])
        self._verbose = verbose
        self._cache = BundleCache(self._config)


    # TODO: Make this an override
    def install_dev_tools(self, bundle: Bundle):
        # Check for a virtualenv and return an error if one is not found
        check_env = subprocess.run(["poetry", "env", "info", "--path"], cwd=self._project_folder, check=False, capture_output=True)  # nosec
        if check_env.returncode != 0:
            raise click.ClickException("No virtualenv found. Please run `poetry install` first.")

        # Read pyproject.toml and remove the sections [tool.poetry.group.switchblade]
        # and [tool.poetry.group.switchblade.dependencies], and add the ones from the
        # bundle.toml file in the commit SHA folder
        self._pyproject_file = self._project_folder / "pyproject.toml"
        self._poetry_lockfile = self._project_folder / "poetry.lock"

        self._pyproject_file_raw_before = self._pyproject_file.read_text(encoding="utf-8")
        if self._poetry_lockfile.exists():
            self._poetry_lockfile_raw_before = self._poetry_lockfile.read_text(encoding="utf-8")
        else:
            self._poetry_lockfile_raw_before = None
        pyproject_config = loads(self._pyproject_file_raw_before)
        pyproject_config["tool"]["poetry"]["group"][
            "switchblade"
        ] = bundle.bundle_config["tool"]["poetry"]["group"]["switchblade"]

        # Also take all other sections beginning with 'tool.' and add them to the pyproject.toml
        # unless there is already a section with the same name in the pyproject.toml
        for section in bundle.bundle_config["tool"]:
            if not section.startswith("poetry") and section not in pyproject_config["tool"]:
                pyproject_config["tool"][section] = bundle.bundle_config["tool"][
                    section
                ]
        with open(self._pyproject_file, "w") as pyproject_toml:
            pyproject_toml.write(dumps(pyproject_config))

        # If the bundle was recently installed, we can optimistically skip the update
        latest_config = self._cache.get_latest_config()
        last_installed_on = latest_config["last_installed_on"]
        if last_installed_on:
            last_installed_on = datetime.strptime(last_installed_on, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            current_datetime = datetime.now(tz=timezone.utc)
            if (current_datetime - last_installed_on).total_seconds() < self.SKIP_UPDATE_IF_INSTALLED_WITHIN:
                print("🔒 bundle dependencies were recently installed, skipping...")
                return

        subprocess.run(
            ["poetry", "update", "--only", "switchblade"],
            cwd=self._project_folder,
            check=True,
            capture_output=False,
        )

        self._cache.update_latest_config({
            "last_installed_on": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })


    # TODO: Place this in a superclass
    def copy_config_files(self, bundle: Bundle):
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


    # TODO: Make this an override (must return False if the linter fails)
    def run_linter(self, bundle: Bundle, linter: dict):
        linter_command_list = linter["command"].split(" ")
        cmd_result = subprocess.run(
            ["poetry", "run", *linter_command_list], cwd=self._project_folder, check=False
        )
        return cmd_result.returncode == 0


    # TODO: Make this an override (must return False if the test fails)
    def run_test(self, bundle: Bundle, test: dict):
        test_command_list = test["command"].split(" ")
        cmd_result = subprocess.run(
            ["poetry", "run", *test_command_list], cwd=self._project_folder, check=False
        )
        return cmd_result.returncode == 0


    # TODO: Make this an override
    def post_cleanup(self, bundle: Bundle, pushed_files: list):
        # Restore the original pyproject.toml
        if self._pyproject_file_raw_before:
            with open(self._pyproject_file, "w") as pyproject_toml:
                pyproject_toml.write(self._pyproject_file_raw_before)
        # Restore the original poetry.lock
        if self._poetry_lockfile_raw_before:
            with open(self._poetry_lockfile, "w") as poetry_lock:
                poetry_lock.write(self._poetry_lockfile_raw_before)


    # TODO: Place this in a superclass
    def lint(self, linter_tool: str):
        # Instantiating a Bundle object will fetch the latest bundle from the source or cache
        latest_bundle = Bundle(self._config)

        bundle_config = latest_bundle.bundle_config
        bundle_mode = bundle_config["bundle"]["mode"]

        if bundle_mode != self.mode:
            click.echo(
                f"⚔️ The Switchblade bundle is for a project of mode {bundle_mode}, but this project is of mode {self.mode}.",
                err=True
            )
            raise click.Abort()

        self._cache.log(f"LINTING {latest_bundle.version}")

        # Show error message if the bundle does not contain any linters
        if "linters" not in bundle_config:
            self._cache.log(f"LINTING {latest_bundle.version} ABORTED_NO_LINTERS_IN_BUNDLE")
            click.secho(
                "⚔️ The Switchblade bundle does not contain any linters.",
                err=True, fg="red"
            )
            raise click.Abort()

        pushed_files = []
        success = False
        try:
            print("⚔️ Switchblade installing dev tools...")
            self.install_dev_tools(latest_bundle)

            print("⚔️ Switchblade copying configuration...")
            pushed_files = self.copy_config_files(latest_bundle)

            # Apply local overrides from .switchblade (merging the linter dicts) if any
            switchblade_linters_config = self._config["linters"] if "linters" in self._config else {}
            merged_linters_config = merge({}, bundle_config["linters"], switchblade_linters_config)

            success = True
            linter_names = merged_linters_config["all"] if linter_tool in ["all", None] else [linter_tool]
            for linter_name in linter_names:
                print(f"⚔️ Switchblade running {linter_name}...", end=" ")
                linter_success = self.run_linter(latest_bundle, merged_linters_config[linter_name])
                print("✅" if linter_success else "❌")
                success = success and linter_success
                self._cache.log(f"RAN {linter_name}")

        except Exception as exc:
            self._cache.log(f"LINTING {latest_bundle.version} FAILED_WITH_EXCEPTION")
            raise click.ClickException(f"Exception detected while running linters, aborting... {exc}")

        finally:
            print("⚔️ Switchblade cleaning up...")
            # Remove the files from the project folder that were added in Step 3
            for file in pushed_files:
                (self._project_folder / file).unlink()
                self._cache.log(f"POPPED {file}")

            self.post_cleanup(latest_bundle, pushed_files)

        if success:
            self._cache.log(f"LINTING {latest_bundle.version} FINISHED_SUCCESSFULLY")
            click.echo("⚔️ Linting finished successfully. 😎")
        else:
            self._cache.log(f"LINTING {latest_bundle.version} FINISHED_WITH_ERRORS")
            click.secho("⚔️ Linting finished with errors. 😭", err=True, fg="red", bold=True)

        return success


    # TODO: Place this in a superclass
    def test(self, test_tool: str):
        # Instantiating a Bundle object will fetch the latest bundle from the source or cache
        latest_bundle = Bundle(self._config)

        bundle_config = latest_bundle.bundle_config
        bundle_mode = bundle_config["bundle"]["mode"]

        if bundle_mode != self.mode:
            click.echo(
                f"⚔️ The Switchblade bundle is for a project of mode {bundle_mode}, but this project is of mode {self.mode}.",
                err=True
            )
            raise click.Abort()

        self._cache.log(f"TESTING {latest_bundle.version}")

        # Show error message if the bundle does not contain any linters
        if "tests" not in bundle_config:
            self._cache.log(f"TESTING {latest_bundle.version} ABORTED_NO_TESTS_IN_BUNDLE")
            click.secho(
                "⚔️ The Switchblade bundle does not contain any tests.",
                err=True, fg="red"
            )
            raise click.Abort()

        pushed_files = []
        success = False
        try:
            print("⚔️ Switchblade installing dev tools...")
            self.install_dev_tools(latest_bundle)

            print("⚔️ Switchblade copying configuration...")
            pushed_files = self.copy_config_files(latest_bundle)

            # Apply local overrides from .switchblade (merging the tests dicts) if any
            bundle_tests_config = bundle_config["tests"]
            switchblade_tests_config = self._config["tests"] if "tests" in self._config else {}
            merged_tests_config = merge({}, bundle_tests_config, switchblade_tests_config)

            success = True
            test_tool_names = merged_tests_config["all"] if test_tool in ["all", None] else [test_tool]
            for test_tool_name in test_tool_names:
                print(f"⚔️ Switchblade running {test_tool_name}...", end = " ")
                test_success = self.run_test(latest_bundle, merged_tests_config[test_tool_name])
                print("✅" if test_success else "❌")
                success = success and test_success
                self._cache.log(f"RAN {test_tool_name}")

        except Exception as exc:
            self._cache.log(f"TESTING {latest_bundle.version} FAILED_WITH_EXCEPTION")
            raise click.ClickException(f"Exception detected while running tests, aborting... {exc}")

        finally:
            print("⚔️ Switchblade cleaning up...")
            # Remove the files from the project folder that were added in Step 3
            for file in pushed_files:
                (self._project_folder / file).unlink()
                self._cache.log(f"POPPED {file}")

            self.post_cleanup(latest_bundle, pushed_files)

        if success:
            self._cache.log(f"TESTING {latest_bundle.version} FINISHED_SUCCESSFULLY")
            click.echo("⚔️ Tests finished successfully. 😎")
        else:
            self._cache.log(f"TESTING {latest_bundle.version} FINISHED_WITH_ERRORS")
            click.secho("⚔️ Tests finished with errors. 😭", err=True, fg="red", bold=True)

        return success
