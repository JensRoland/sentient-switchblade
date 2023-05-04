<!-- markdownlint-disable first-line-h1 line-length no-inline-html -->
<p align="center">
  <a href="https://github.com/JensRoland/sentient-switchblade">
    <img src="https://jensroland.com/switchblade/assets/switchblade-logotype.png" width="415px" alt="Switchblade logo" />
  </a>
</p>

<h3 align="center">Unleash Dev Tool Mastery with a Flick of Your Wrist</h3>
<p align="center">Created by <a href="https://jensroland.com/">Jens Roland</a></p>

<br />

## ⚔️ What is Switchblade?

Switchblade is a command line tool that lets you install and run dev tools from a central repository, and configure them in a standardised way across all your projects.

## Try it

To use the included `python-poetry-base` bundle for Python, create a `.switchblade` file in your project root:

```toml
[switchblade]
bundle = "gh:jensroland/sentient-switchblade/bundles/python-poetry-base"
mode = "python-poetry"
```

Then, install Switchblade in your project and call `swb lint` to run the standard Python linters configured in the base bundle:

```shell
# Install Switchblade
poetry add -G dev sentient-switchblade

# Run linters from the bundle
poetry run swb lint
```

That's it! :tada: Switchblade will fetch the bundle from Github, install the tools specified in the bundle, and run them with the configurations specified in the bundle. No need to install or configure anything yourself, and no need to commit any dev tooling to your project repo.

**Note**: The base bundle assumes that your source code lives under `src/` and your tests under `tests/`, but it is only meant as an example. To specify your own dev tools and tailor them to your needs and project structure, create your own custom bundle (see below).

## Who is this for?

Switchblade was born from the question: *"How do I ensure that I'm using the same linting and testing configurations across all of my project repositories?"* Are all of your Python repos using the same version of `Black`? Maybe you switched to `flake8` on your newer repos but never updated the old ones? Sure, maybe it doesn't matter very much if your tooling deviates a little between your personal projects, but how about this: when your company's DevSecOps team updated all the templates to include scans for known vulnerabilities and credential leaks, did you remember to update all of your repos? And if not, how would you even know?

To complicate matters, developer tooling is not simply about choosing a particular linter and firing it up. It's also how you configure it -- maximum line lengths, whether to use single or double quotes, what rules to ignore entirely -- as well as which arguments to pass when you invoke it.

<!-- Every software engineering organisation has to deal with these issues, and while many solutions exist, they are hardly perfect:

1. Provide project templates with dev tooling built-in, and use those templates to create new projects. This works well initially, but results in duplicated configuration files and makes all subsequent configuration updates both time consuming and error prone, since they have to be made in all projects at once.
2. Let configs be duplicated across projects and use [a meta-repo tool](https://github.com/mateodelnorte/meta) to perform cross-repo updates. This requires a non-trivial amount of setup and maintenance, and updating a dev configuration still requires committing changes in every repo.
3. Combine all dev tooling in a package and install it in every project. This works for some types of tooling, but many tools require their config files to exist in the project root rather than inside a package. It also usually requires committing changes (e.g. the updated lockfile) in every repo to get the latest configurations.
4. Use a monorepo; have one set of dev tools included in the repo and use it for everything. This can actually be a great solution, but it's not always possible or desirable to use a monorepo.
5. Something custom involving Docker containers and prebaked images with dev tools. This involves a lot of complexity and overhead, plus you get all the limitations of the package solution. -->

In an ideal world, dev tooling would not be checked into version control (*seriously*) but rather **fetched on demand from a centrally managed dev tooling repository, and configured and invoked in exactly the same way in every repo, every time**. This would allow for a single source of truth for all dev tooling, and would make it easy to update configurations across all projects.

To achieve this however, you would need some kind of small helper tool to abstract away the fetching, configuring and invoking of your centrally curated 'bundles' of dev tools.

Switchblade is that tool.

## Custom bundles

To create your own custom bundle with the dev tools and configurations you need, simply create a new Github repo and add a `bundle.toml` file to it:

```toml
[bundle]
name = "my-dev-tool-bundle"
mode = "python-poetry"
schema_version = "1.0.0"

# Linters
[linters]
all = ["pylint"]

[linters.pylint]
command = "pylint src"

# Tests
[tests]
all = ["pytest"]

[tests.pytest]
command = "pytest -c pyproject.toml tests"

# Extensions to pyproject.toml
[tool.poetry.group.switchblade]
optional = true

[tool.poetry.group.switchblade.dependencies]
pylint = "^2.17.2"
pytest = "^7.3.1"

[tool.pytest.ini_options]
pythonpath = "src"
```

For each linter you want to add, specify a `[linters.<toolname>]` section with a `command` key. The `command` value will be invoked by Switchblade when you run `swb lint <toolname>`.

The `[linters]` section specifies which linters should be invoked (and in which order) when you run `swb lint` or `swb lint all`.

The same goes for tests: specify a `[tests.<toolname>]` section with a `command` key, and add the tool to the `[tests]` section to have it invoked when you run `swb test` or `swb test all`.

### Tool configuration

Anything in the `bundle.toml` file under a `tool.*` section will be temporarily added to the project's `pyproject.toml` file under that section. This allows you to add dependencies and configuration options to all your projects without having to manually edit all the individual `pyproject.toml` files.

If you prefer having separate config files, or for tools which do not support `pyproject.toml` configuration, simply add any config files you need in the same folder as the `bundle.toml` file. E.g. you might define a `.pylintrc` in the bundle repo:

```ini
[MAIN]
[MESSAGES CONTROL]
disable=
    C0111,  # missing-docstring
    C0114,  # missing-module-docstring
    C0115,  # missing-class-docstring
    C0116,  # missing-function-docstring
    W0613,  # unused-argument
```

Now, when you want to use your custom dev tool bundle in a project, simply point to the repo in the project `.switchblade` file as in the example above. Swichblade will then fetch and install the tools you specified in the bundle and run them with the configurations you specified.

### Per-project overrides

To override the bundle configuration for a specific dev tool in one of your project repos, simply check in the tool dependencies and configuration files in the project repo as you normally would - Switchblade will still invoke the dev tool, but it will not overwrite any existing config files or `[tool.*]` sections in your `pyproject.toml` file. Be aware that this does not 'extend' the configuration from the bundle, but replaces that tool configuration entirely, so this feature should be used with caution.

To override the command or the list of linters to run, add the corresponding sections (e.g. `[linters]` or `[linters.pylint]` in the project `.switchblade` file. Switchblade will automatically merge (in this case it does extend rather than replace) the bundle config and Switchblade config before invoking any of the tools.

## Prerequisites

- [Python 3.7+](https://www.python.org/downloads/)

Currently, you need Python since you install Switchblade with pip. This may change in the future.

## Features

- CLI command `swb lint` to run linters
- CLI command `swb test` to run tests
- Project 'modes' supported: Currently only `python-poetry` is supported, but more will be added soon.

## Development

Install dependencies:

```shell
> poetry install
```

Run unit tests:

```shell
> poetry run pytest -c pyproject.toml --cov-report=term --cov=src tests
```
