import click
import os
import shutil

from datetime import datetime, timezone
from github import Github
from mergedeep import merge
from pathlib import Path
from tomlkit import dumps, loads

from switchbladecli.utils import hash_dir

BUNDLE_CONFIG_FILES = ["bundle.toml"]
CACHE_FOLDERNAME = ".switchblade-cache"
LATEST_CONFIG_FILENAME = "latest.toml"
UPDATE_LOG_FILENAME = "update.log"


class Bundle:
    """A bundle of dev tools and configs.
    """

    def __init__(self, switchblade_config: dict, version: str = None):
        """Initialize a Bundle object.

        If version is None, the latest bundle will be used (conditionally fetched and cached).

        If a version is passed:
            1. Tries to fetch a bundle with that version from the cache.
            2. If the bundle doesn't exist, an exception is raised.

        Args:
            switchblade_config (dict): The switchblade config.
            version (str, optional): The version of the bundle to fetch. Defaults to None.
        """
        self._switchblade_config = switchblade_config
        if version is None:
            click.echo("⚔️ Switchblade initializing bundle...")
            cache = BundleCache(self._switchblade_config)
            bundle = self._fetch_latest(cache)
            self.version = bundle.version
            self.bundle_folder = bundle.bundle_folder
            self.bundle_config = bundle.bundle_config

        else:
            click.echo(f"⚔️ Switchblade initializing bundle with version {version}...")
            self.version = version
            self.bundle_folder = self._bundle_folder_from_version(version)
            self.bundle_config = self._load_bundle_config()
    

    def _load_bundle_config(self) -> dict:
        """Get the bundle config from the config file."""
        bundle_config_file = None
        for bundle_config_file_name in BUNDLE_CONFIG_FILES:
            bundle_config_file = self.bundle_folder / bundle_config_file_name
            if bundle_config_file.exists():
                break
        if bundle_config_file is None or not bundle_config_file.exists():
            raise FileNotFoundError(f"No bundle config file found in bundle {self.version}")
        return loads(bundle_config_file.read_text(encoding="utf-8"))
    
    
    def _bundle_folder_from_version(self, version) -> Path:
        """Get the bundle folder."""
        return Path(CACHE_FOLDERNAME) / version


    def get_files(self) -> list:
        """Get the list of files (excluding the config) in the bundle.
        
        Returns a list of file paths relative to the bundle folder.
        """
        return [str(file.relative_to(self.bundle_folder)) for file in self.bundle_folder.rglob("*") if file.name not in BUNDLE_CONFIG_FILES]


    def _fetch_latest(self, cache: "BundleCache") -> "Bundle":
        """Conditionally fetch and return the latest bundle.
        """
        bundle_source_uri = self._switchblade_config["switchblade"]["bundle"]
        click.echo("⚔️ Switchblade checking for updates...")

        # Check the remote version to see if we need to update
        remote_version = None
        pygithub = None
        if bundle_source_uri.startswith("gh:"):
            try:
                # Init the Github API
                pygithub = Github(os.environ.get("GITHUB_TOKEN"))
                # Get the org name, repo name and folder(s)
                org_name, repo_name, *folder = bundle_source_uri[3:].split("/")
                # Get the commit SHA from the repo (default branch)
                repo = pygithub.get_repo(f"{org_name}/{repo_name}")
                remote_version = repo.get_branch(repo.default_branch).commit.sha
            except Exception as exc:
                # If something went wrong fetching from Github,
                # we use the latest cached bundle if it exists
                latest_cached_version = cache.get_latest_version()
                if latest_cached_version is not None:
                    click.echo(f"⚔️ Switchblade failed to fetch remote bundle, using cached version {latest_cached_version} instead.")
                    cache.log(f"FETCH FAILED_WITH_FALLBACK")
                    return Bundle(self._switchblade_config, latest_cached_version)
                else:
                    # If there is no cached bundle, raise the exception
                    cache.log(f"FETCH FAILED")
                    raise click.ClickException(f"Remote bundle repo '{bundle_source_uri}' could not be fetched: {exc}")
        else:
            # If the folder doesn't exist, raise an exception
            bundle_source_folder = Path(bundle_source_uri)
            if not bundle_source_folder.exists():
                raise FileNotFoundError(f"Bundle folder {bundle_source_uri} does not exist.")
            remote_version = hash_dir(bundle_source_uri)

        cache.log(f"UPDATING {remote_version}")
        
        # Check if the latest version from the remote is already cached
        # (does not necessarily have to be the most recently fetched bundle from 'latest.toml')
        if cache.has_bundle(remote_version):
            # If the latest cached bundle is up to date, just return it
            click.echo(f"⚔️ Switchblade cache already contains version {remote_version}")
            cache.log(f"UPDATING {remote_version} SKIPPED_ALREADY_CACHED")
            return Bundle(self._switchblade_config, remote_version)

        # If the cache is stale, update it
        click.echo(f"⚔️ Switchblade updating tool bundle to version {remote_version}...")
        bundle_folder = self._bundle_folder_from_version(remote_version)
        if bundle_source_uri.startswith("gh:"):
            # Create the bundle folder
            bundle_folder.mkdir(parents=True)
            # Get the contents of the repo
            org_name, repo_name, *folder = bundle_source_uri[3:].split("/")
            repo = pygithub.get_repo(f"{org_name}/{repo_name}")
            repo_contents = repo.get_contents("/".join(folder), ref=remote_version)
            # Download all the files
            for repo_asset in repo_contents:
                with open(bundle_folder / repo_asset.name, "wb") as file:
                    file.write(repo_asset.decoded_content)

        else:
            # If the source is a local folder, copy it to the cache
            shutil.copytree(bundle_source_uri, bundle_folder)

        cache.log(f"UPDATING {remote_version} SUCCEEDED")

        new_bundle = Bundle(self._switchblade_config, remote_version)
        cache.set_latest_config(new_bundle)

        # Finally, return the fetched bundle
        return new_bundle


class BundleCache:

    def __init__(self, switchblade_config: dict):
        self._switchblade_config = switchblade_config
        self._project_folder = Path(self._switchblade_config.get("project_dir"))
        self._cache_folder = self._initialize_cache_folder(self._project_folder)


    def _initialize_cache_folder(self, project_folder: Path):
        """Initialize a new cache folder if it doesn't exist yet.

        Creates:
            - The cache folder
            - A .gitignore file in the cache folder with an asterisk in it
            - An update.log file in the cache folder
        """
        cache_folder = project_folder / CACHE_FOLDERNAME
        if not cache_folder.exists():
            # Make sure the cache folder exists
            cache_folder.mkdir()
            # Add a .gitignore file with an asterisk in it to ensure that the
            # cache folder is never committed to git
            with open(cache_folder / ".gitignore", "w") as gitignore:
                gitignore.write("*")

        # Make sure the update.log file exists
        update_log = cache_folder / UPDATE_LOG_FILENAME
        if not update_log.exists():
            update_log.touch()
        
        return cache_folder


    def get_bundle(self, version: str) -> Bundle:
        """Get a bundle from the cache."""
        return Bundle(self._switchblade_config, version)


    def get_bundles(self) -> list:
        """Get all bundles in the cache."""
        bundles = []
        for bundle_folder in os.listdir(self._cache_folder):
            # Skip non-folders
            if not (self._cache_folder / bundle_folder).is_dir():
                continue
            bundles.append(Bundle(self._switchblade_config, bundle_folder))
        return bundles


    def _get_latest_config_file(self, check_exists: bool = True) -> Path:
        """Get the latest config file."""
        latest_config_file = self._cache_folder / LATEST_CONFIG_FILENAME
        if check_exists and not latest_config_file.exists():
            return None
        return latest_config_file


    def get_latest_config(self) -> dict:
        """Get the latest config."""
        latest_config_file = self._get_latest_config_file()
        # If the latest.toml file doesn't exist, return None
        if latest_config_file is None:
            return None
        latest = loads(latest_config_file.read_text(encoding="utf-8"))
        return latest["latest"]


    def set_latest_config(self, bundle: Bundle):
        """Set the latest config."""
        latest_config_file = self._get_latest_config_file(False)
        with open(latest_config_file, "w") as latest_toml:
            latest_toml.write(
                dumps(
                    {
                        "latest": {
                            "commit_sha": bundle.version,
                            "fetched_on": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "files": bundle.get_files(),
                            "last_installed_on": ""
                        }
                    }
                )
            )


    def update_latest_config(self, updated_latest: dict):
        """Update the latest config, merging with updated dict."""
        latest_config_file = self._get_latest_config_file(False)
        latest_config = self.get_latest_config()
        merge(latest_config, updated_latest)
        with open(latest_config_file, "w") as latest_toml:
            latest_toml.write(
                dumps(
                    {
                        "latest": latest_config
                    }
                )
            )


    def get_latest_version(self) -> str:
        """Get the latest version."""
        latest_config = self.get_latest_config()
        if latest_config is None:
            return None
        return latest_config["commit_sha"]


    def get_latest_bundle(self) -> Bundle:
        """Get the latest bundle."""
        latest_config = self.get_latest_config()
        if latest_config is None:
            return None
        return self.get_bundle(latest_config["commit_sha"])


    def log(self, message):
        current_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with open(self._cache_folder / UPDATE_LOG_FILENAME, "a") as update_log:
            update_log.write(f"[{current_time}] {message}\n")


    def has_bundle(self, version: str) -> bool:
        """Check if a version is in the cache."""
        return (self._cache_folder / version).exists()


    def cleanup(self):
        """Remove all bundles from cache except the latest.
        """
        latest_version = self.get_latest_version()
        bundles = self.get_bundles()
        for bundle in bundles:
            if bundle.version != latest_version:
                shutil.rmtree(bundle.bundle_folder)
