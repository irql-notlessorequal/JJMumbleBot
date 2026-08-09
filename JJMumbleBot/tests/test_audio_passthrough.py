import os

import opuslib

from JJMumbleBot.lib.audio import audio_passthrough as ap
from mumble import MumbleUDP_pb2
from mumble import sendaudio as sendaudio_module

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
TONE_OGG = os.path.join(FIXTURE_DIR, "tone.ogg")
OPUSLIB_OK = True


class TestOpusFrameDuration:
    def test_common_20ms(self):
        assert ap.opus_frame_duration(bytes([0x88])) == 0.020

    def test_60ms_full_bandwidth(self):
        assert ap.opus_frame_duration(bytes([0x98])) == 0.060

    def test_10ms(self):
        assert ap.opus_frame_duration(bytes([0x08])) == 0.020

    def test_25ms(self):
        assert ap.opus_frame_duration(bytes([0xA0])) == 0.0025

    def test_stereo_lacing(self):
        assert ap.opus_frame_duration(bytes([0x89])) == 0.040

    def test_empty(self):
        assert ap.opus_frame_duration(b"") == 0.0


class TestOggDemuxer:
    def test_demux_fixture_small_chunks(self):
        with open(TONE_OGG, "rb") as f:
            data = f.read()
        demuxer = ap.OggDemuxer()
        packets = []
        assert len(data) > 0
        while True:
            chunk = data[:7]
            data = data[7:]
            packets.extend(demuxer.feed(chunk))
            if not data:
                break
        assert len(packets) > 0
        for packet in packets:
            assert not packet.startswith(b"OpusHead")
            assert not packet.startswith(b"OpusTags")
            assert ap.opus_frame_duration(packet) > 0.0

    def test_demux_fixture_single_chunk(self):
        with open(TONE_OGG, "rb") as f:
            packets = ap.OggDemuxer().feed(f.read())
        assert len(packets) > 0

    def test_packets_are_valid_opus(self):
        if not OPUSLIB_OK:
            return
        with open(TONE_OGG, "rb") as f:
            data = f.read()
        packets = []
        demuxer = ap.OggDemuxer()
        for chunk_start in range(0, len(data), 257):
            packets.extend(demuxer.feed(data[chunk_start : chunk_start + 257]))
        decoder = opuslib.Decoder(48000, 2)
        for packet in packets:
            decoded = decoder.decode(packet, 960)
            assert isinstance(decoded, (bytes, bytearray))
            assert len(decoded) > 0


class TestIsOpusSource:
    def test_opus_fixture(self):
        assert ap.is_opus_source(TONE_OGG) is True

    def test_non_opus_file(self):
        this_file = os.path.join(os.path.dirname(__file__), "test_audio_passthrough.py")
        assert ap.is_opus_source(this_file) is False


class TestSendPassthroughAudio:
    def test_packets_assembled_from_raw_frames(self):
        import types

        class StubLog:
            def debug(self, *a, **k):
                pass

        class StubUdpThread:
            def __init__(self):
                self.sent = []

            def encrypt_and_send_message(self, msg):
                self.sent.append(msg)

        class StubMumble:
            positional = None
            force_tcp_only = False

            def __init__(self):
                self.Log = StubLog()
                self.udp_thread = StubUdpThread()
                self.udp_active = True

        ap.install_passthrough_send_audio()
        send_audio_class = sendaudio_module.SendAudio

        sa = send_audio_class(StubMumble(), 0.02, 128000)
        sa.codec = types.SimpleNamespace(opus=True)
        sa._create_encoder()

        fps = [1.0]

        def fake_time():
            fps[0] += 0.1
            return fps[0]

        ap.time = fake_time

        frames = [bytes([0x88])] * 3
        for frame in frames:
            sa.add_opus(frame, 0.020)

        sa._send_opus_audio()

        sent = sa.mumble_object.udp_thread.sent
        assert len(sent) == 3
        frame_numbers = []
        for msg in sent:
            assert msg[0] == 0
            audio = MumbleUDP_pb2.Audio()
            audio.ParseFromString(msg[1:])
            frame_numbers.append(audio.frame_number)
            assert bytes(audio.opus_data) == bytes([0x88])
        assert frame_numbers == [120, 140, 160]

        ap.time = __import__("time").time

    def test_buffer_size_includes_opus_frames(self):
        import types

        class StubLog:
            def debug(self, *a, **k):
                pass

        class StubUdpThread:
            def encrypt_and_send_message(self, msg):
                pass

        class StubMumble:
            positional = None
            force_tcp_only = False
            udp_active = True

            def __init__(self):
                self.Log = StubLog()
                self.udp_thread = StubUdpThread()

        ap.install_passthrough_send_audio()
        send_audio_class = sendaudio_module.SendAudio

        sa = send_audio_class(StubMumble(), 0.02, 128000)
        sa.codec = types.SimpleNamespace(opus=True)
        sa._create_encoder()

        sa.add_opus(bytes([0x88]), 0.020)
        sa.add_opus(bytes([0x88]), 0.020)
        assert sa.get_buffer_size() == 0.040

        sa.clear_buffer()
        assert sa.get_buffer_size() == 0.0