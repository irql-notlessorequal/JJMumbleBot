from JJMumbleBot.lib.utils.runtime_utils import parse_remote_components


class TestParseRemoteComponents:
    def test_comma_separated(self):
        assert parse_remote_components("ejs:npm, ejs:github") == [
            "ejs:npm",
            "ejs:github",
        ]

    def test_space_separated(self):
        assert parse_remote_components("ejs:npm ejs:github") == [
            "ejs:npm",
            "ejs:github",
        ]

    def test_blank(self):
        assert parse_remote_components("") == []
        assert parse_remote_components(None) == []
        assert parse_remote_components("   ") == []

    def test_extra_whitespace(self):
        assert parse_remote_components(" ejs:npm  ,   ejs:github ") == [
            "ejs:npm",
            "ejs:github",
        ]

    def test_brackets_and_quotes(self):
        assert parse_remote_components("['ejs:npm', 'ejs:github']") == [
            "ejs:npm",
            "ejs:github",
        ]