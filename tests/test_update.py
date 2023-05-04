from switchbladecli.cli.config import find_config_file, get_switchblade_config
from switchbladecli.cli.update import cmd_update
from switchbladecli.cli.bundle_cache import BundleCache

TEST_PREVIOUS_BUNDLE_VERSION = "12340000"
TEST_BUNDLE_VERSION = "12345678"

def test_update_fetches_bundle(project, patched_pygithub):
    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)
    cache = BundleCache(config)

    assert cache.has_bundle(TEST_BUNDLE_VERSION) == False

    cmd_update(False, project, config)

    assert patched_pygithub.return_value.get_repo.return_value.get_branch.call_count == 1
    assert patched_pygithub.return_value.get_repo.return_value.get_contents.call_count == 1

    assert cache.has_bundle(TEST_BUNDLE_VERSION) == True

    bundle = cache.get_bundle(TEST_BUNDLE_VERSION)
    bundle_files = bundle.get_files()

    assert ".flake8" in bundle_files
    assert ".pre-commit-config.yaml" in bundle_files
    assert ".pylintrc" in bundle_files
    assert ".ruff.toml" in bundle_files

    # The get_files() method should not return the bundle.toml file
    assert "bundle.toml" not in bundle_files


def test_update_updates_stale_cached_bundle(project_with_cached_bundle, patched_pygithub):
    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project_with_cached_bundle), config_file)
    cache = BundleCache(config)

    assert cache.has_bundle(TEST_PREVIOUS_BUNDLE_VERSION) == True
    assert cache.has_bundle(TEST_BUNDLE_VERSION) == False

    cmd_update(False, project_with_cached_bundle, config)

    assert patched_pygithub.return_value.get_repo.return_value.get_branch.call_count == 1
    assert patched_pygithub.return_value.get_repo.return_value.get_contents.call_count == 1

    assert cache.has_bundle(TEST_BUNDLE_VERSION) == True

    bundle = cache.get_latest_bundle()
    assert bundle.version == TEST_BUNDLE_VERSION

    bundle_files = bundle.get_files()

    assert ".flake8" in bundle_files
    assert ".pre-commit-config.yaml" in bundle_files
    assert ".pylintrc" in bundle_files
    assert ".ruff.toml" in bundle_files

    # The get_files() method should not return the bundle.toml file
    assert "bundle.toml" not in bundle_files


def test_update_reuses_bundle_if_cached(project, patched_pygithub):
    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project), config_file)
    cache = BundleCache(config)

    cmd_update(False, project, config)

    assert cache.has_bundle(TEST_BUNDLE_VERSION) == True

    patched_pygithub.reset_mock()

    cmd_update(False, project, config)

    assert patched_pygithub.return_value.get_repo.return_value.get_branch.call_count == 1
    assert patched_pygithub.return_value.get_repo.return_value.get_contents.call_count == 0


def test_update_uses_cached_bundle_if_remote_unavailable(project_with_cached_bundle, patched_pygithub_with_exception):
    config_file = find_config_file(False, None)
    config = get_switchblade_config(False, str(project_with_cached_bundle), config_file)
    cache = BundleCache(config)

    assert cache.has_bundle(TEST_PREVIOUS_BUNDLE_VERSION) == True

    cmd_update(False, project_with_cached_bundle, config)

    assert cache.get_latest_version() == TEST_PREVIOUS_BUNDLE_VERSION
    assert cache.has_bundle(TEST_BUNDLE_VERSION) == False
    assert len(cache.get_bundles()) == 1
    assert cache.get_latest_bundle().version == TEST_PREVIOUS_BUNDLE_VERSION
