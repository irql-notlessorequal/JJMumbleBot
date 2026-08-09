import types

import pytest
import yt_dlp

from JJMumbleBot.plugins.core.server_tools.utility import server_tools_utility as st_utility
from JJMumbleBot.plugins.core.server_tools.utility import settings


class FakeUpdateInfo:
    def __init__(self, version):
        self.version = version


class FakeUpdater:
    def __init__(self, latest_version):
        self._latest_version = latest_version
        self.calls = 0

    def query_update(self):
        self.calls += 1
        if self._latest_version is None:
            return None
        return FakeUpdateInfo(self._latest_version)


def reset_cache(installed=None, latest=None):
    settings.ytdlp_update_check["timestamp"] = 0
    settings.ytdlp_update_check["installed_version"] = installed
    settings.ytdlp_update_check["latest_version"] = latest


@pytest.fixture(autouse=True)
def reset_state():
    reset_cache()
    yield
    reset_cache()


def patch_ytdlp(monkeypatch, installed, latest):
    updater = FakeUpdater(latest)

    def fake_youtube_dl(*args, **kwargs):
        return object()

    def fake_updater(ydl):
        return updater

    monkeypatch.setattr(yt_dlp.version, "__version__", installed)
    monkeypatch.setattr(yt_dlp, "YoutubeDL", fake_youtube_dl)
    monkeypatch.setattr(yt_dlp.update, "Updater", fake_updater)
    return updater


class TestCheckYtdlpUpdate:
    def test_outdated_returns_versions(self, monkeypatch):
        patch_ytdlp(monkeypatch, installed="2026.07.04", latest="2026.08.01")
        result = st_utility.check_ytdlp_update(force=True)
        assert result == ("2026.07.04", "2026.08.01")

    def test_up_to_date_returns_none(self, monkeypatch):
        patch_ytdlp(monkeypatch, installed="2026.08.01", latest="2026.08.01")
        assert st_utility.check_ytdlp_update(force=True) is None

    def test_no_update_info_returns_none(self, monkeypatch):
        patch_ytdlp(monkeypatch, installed="2026.07.04", latest=None)
        assert st_utility.check_ytdlp_update(force=True) is None

    def test_failure_returns_none(self, monkeypatch):
        def boom(*args, **kwargs):
            raise RuntimeError("network down")

        monkeypatch.setattr(yt_dlp, "YoutubeDL", boom)
        assert st_utility.check_ytdlp_update(force=True) is None

    def test_cached_result_not_requeried(self, monkeypatch):
        updater = patch_ytdlp(monkeypatch, installed="2026.07.04", latest="2026.08.01")
        assert st_utility.check_ytdlp_update(force=True) == (
            "2026.07.04",
            "2026.08.01",
        )
        st_utility.check_ytdlp_update()
        assert updater.calls == 1

    def test_cached_up_to_date_returns_none(self):
        reset_cache(installed="2026.07.04", latest="2026.07.04")
        settings.ytdlp_update_check["timestamp"] = 42
        assert st_utility.check_ytdlp_update() is None

    def test_force_bypasses_cache(self, monkeypatch):
        updater = patch_ytdlp(monkeypatch, installed="2026.07.04", latest="2026.08.01")
        reset_cache(installed="2026.07.04", latest="2026.08.01")
        settings.ytdlp_update_check["timestamp"] = 42
        st_utility.check_ytdlp_update()
        assert updater.calls == 1

    def test_stale_cache_requeries(self, monkeypatch):
        updater = patch_ytdlp(monkeypatch, installed="2026.07.04", latest="2026.08.01")
        reset_cache(installed="2026.07.04", latest="2026.08.01")
        settings.ytdlp_update_check["timestamp"] = 1
        st_utility.check_ytdlp_update()
        assert updater.calls == 1


class TestYtdlpUpdateMessage:
    def test_message_contains_versions(self):
        msg = st_utility.ytdlp_update_message("2026.07.04", "2026.08.01")
        assert "2026.07.04" in msg
        assert "2026.08.01" in msg
        assert "pip install -U yt-dlp" in msg