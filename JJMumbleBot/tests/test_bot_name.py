import os
from JJMumbleBot.lib.utils.runtime_utils import resolve_bot_name


class TestResolveBotName:
    def test_literal_name(self):
        assert resolve_bot_name("JJMumbleBot") == "JJMumbleBot"

    def test_name_file_pick(self, tmp_path):
        name_file = tmp_path / "names.txt"
        name_file.write_text("Alpha\nBeta\n\n# comment\nGamma\n")
        for _ in range(20):
            assert resolve_bot_name(str(name_file)) in {"Alpha", "Beta", "Gamma"}

    def test_empty_name_file(self, tmp_path):
        name_file = tmp_path / "empty.txt"
        name_file.write_text("# only comments\n\n")
        try:
            resolve_bot_name(str(name_file))
            assert False, "Expected ValueError for an empty name file"
        except ValueError:
            pass
