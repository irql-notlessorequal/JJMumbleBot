from JJMumbleBot.lib.audio.audio_interface import format_http_headers


class TestFormatHttpHeaders:
    def test_empty(self):
        assert format_http_headers(None) == ""
        assert format_http_headers({}) == ""

    def test_crlf_format(self):
        out = format_http_headers(
            {"Referer": "https://odysee.com/", "User-Agent": "test-agent"}
        )
        assert out == "Referer: https://odysee.com/\r\nUser-Agent: test-agent\r\n"