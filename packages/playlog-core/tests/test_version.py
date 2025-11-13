from playlog import __version__


def test_version_is_semver_like() -> None:
    assert __version__.count(".") == 2
