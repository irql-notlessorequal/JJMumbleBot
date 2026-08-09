import socket
import struct
import subprocess as sp
from os import path
from time import time

from mumble import MumbleUDP_pb2
from mumble import sendaudio as sendaudio_module
from mumble.constants import (
    SEQUENCE_DURATION,
    SEQUENCE_RESET_INTERVAL,
    TCP_MSG_TYPE,
    UDP_MSG_TYPE,
)

MAX_OPUS_PACKET_SIZE = 900


def format_http_headers(headers):
    if not headers:
        return ""
    return "".join(f"{key}: {value}\r\n" for key, value in headers.items())


def opus_frame_duration(payload) -> float:
    """Return the total audio duration (in seconds) of one Opus packet.

    The duration is derived from the TOC byte in the packet header.
    """
    if not payload:
        return 0.0
    toc = payload[0]
    config = (toc >> 3) & 0x1F
    if config < 20:
        ms = (10, 20, 40, 60)[config % 4]
    else:
        ms = (2.5, 5, 10, 20)[config % 4]
    frame_count = (1, 2, 3, 2)[toc & 0x03]
    return (ms * frame_count) / 1000.0


class OggDemuxer:
    """Incremental Ogg demuxer that yields complete Opus audio packets.

    Fully contained packet boundaries are required because a raw Opus stream is
    not self-delimiting. The source is demuxed with ffmpeg (`-acodec copy -f
    ogg`) and this parser reads the Ogg lacing/segment table to reconstruct the
    original packets, discarding the `OpusHead`/`OpusTags` identification pages.
    """

    def __init__(self):
        self._buffer = bytearray()
        self._pending = None

    def feed(self, chunk) -> list:
        self._buffer += chunk
        packets = []
        while True:
            page = self._read_page()
            if page is None:
                break
            seg_table, body, _ = page
            offset = 0
            for lace in seg_table:
                if self._pending is not None:
                    self._pending += body[offset : offset + lace]
                    offset += lace
                    if lace < 255:
                        pkt = bytes(self._pending)
                        self._pending = None
                        self._push_out(packets, pkt)
                else:
                    if lace < 255:
                        pkt = bytes(body[offset : offset + lace])
                        offset += lace
                        self._push_out(packets, pkt)
                    else:
                        self._pending = bytearray(body[offset : offset + lace])
                        offset += lace
        return packets

    def _push_out(self, packets, pkt):
        if pkt.startswith(b"OpusHead") or pkt.startswith(b"OpusTags"):
            return
        packets.append(pkt)

    def _read_page(self):
        buf = self._buffer
        if len(buf) < 27:
            return None
        if bytes(buf[:4]) != b"OggS":
            idx = bytes(buf).find(b"OggS")
            if idx == -1:
                del buf[:-3]
                return None
            del buf[:idx]
            if len(buf) < 27:
                return None
        page_segments = buf[26]
        header_len = 27 + page_segments
        if len(buf) < header_len:
            return None
        seg_table = bytes(buf[27:header_len])
        seg_total = sum(seg_table)
        body_len = header_len + seg_total
        if len(buf) < body_len:
            return None
        header_type = buf[5]
        body = bytes(buf[header_len:body_len])
        del buf[:body_len]
        return (seg_table, body, header_type)


def build_ffmpeg_params(
    audio_lib_path, uri, skipto=0, quiet=True, http_headers=None
):
    params = [audio_lib_path]
    if quiet:
        params.extend(["-loglevel", "error"])
    if uri.startswith(("http://", "https://")):
        params.extend(
            [
                "-reconnect",
                "1",
                "-reconnect_streamed",
                "1",
                "-reconnect_delay_max",
                "2",
            ]
        )
    if skipto > 0:
        params.extend(["-ss", f"{skipto}"])
    header_string = format_http_headers(http_headers)
    if header_string:
        params.extend(["-headers", header_string])
    params.extend(["-nostdin", "-i", uri])
    params.extend(["-vn", "-acodec", "copy", "-f", "ogg", "-"])
    return params


def is_opus_source(uri, audio_lib_path="ffmpeg", http_headers=None) -> bool:
    probe = "ffprobe"
    if "/" in audio_lib_path:
        probe = path.join(path.dirname(audio_lib_path), "ffprobe")
    cmd = [
        probe,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        uri,
    ]
    try:
        out = sp.run(cmd, capture_output=True, text=True, timeout=15)
        return out.returncode == 0 and out.stdout.strip().lower() == "opus"
    except Exception:
        return False


def _ensure_opus_buffers(self):
    if not hasattr(self, "_opus_data"):
        self._opus_data = []
        self._opus_durations = []


def add_opus(self, payload, duration):
    _ensure_opus_buffers(self)
    self.queue_empty.clear()
    self.lock.acquire()
    self._opus_data.append(payload)
    self._opus_durations.append(duration)
    self.lock.release()


def _pop_opus_packet(self):
    _ensure_opus_buffers(self)
    payload = bytearray()
    packed_duration = 0.0
    self.lock.acquire()
    while self._opus_data and packed_duration < self.audio_per_packet:
        payload += self._opus_data.pop(0)
        packed_duration += self._opus_durations.pop(0)
    self.lock.release()
    return (bytes(payload), packed_duration)


def _send_opus_audio(self):
    """Send buffered raw Opus frames instead of re-encoding PCM.

    Mirrors SendAudio.send_audio()'s sequencing so that passthrough frames and
    the regular PCM/encode path stay interchangeable.
    """
    _ensure_opus_buffers(self)
    if not (self.encoder and len(self._opus_data) > 0):
        self.queue_empty.set()
        return ()

    while len(self._opus_data) > 0 and (
        self.sequence_last_time + self.audio_per_packet <= time()
    ):
        current_time = time()
        payload, packed_duration = _pop_opus_packet(self)
        if self.sequence_last_time + SEQUENCE_RESET_INTERVAL <= current_time:
            self.sequence = 0
            self.sequence_start_time = current_time
            self.sequence_last_time = current_time
        elif (
            self.sequence_last_time + (self.audio_per_packet * 2) <= current_time
        ):
            self.sequence = int(
                (current_time - self.sequence_start_time) / SEQUENCE_DURATION
            )
            self.sequence_last_time = self.sequence_start_time + (
                self.sequence * SEQUENCE_DURATION
            )
        else:
            self.sequence += int(max(packed_duration / SEQUENCE_DURATION, 1))
            self.sequence_last_time = self.sequence_start_time + (
                self.sequence * SEQUENCE_DURATION
            )

        audio_pb = MumbleUDP_pb2.Audio()
        audio_pb.target = self.target
        audio_pb.frame_number = self.sequence
        audio_pb.opus_data = payload
        if self.mumble_object.positional:
            audio_pb.positional_data = self.mumble_object.positional
        msg = struct.pack("!B", UDP_MSG_TYPE.Audio) + audio_pb.SerializeToString()

        if self.mumble_object.force_tcp_only:
            tcppacket = struct.pack("!HL", TCP_MSG_TYPE.UDPTunnel, len(msg)) + msg
            while len(tcppacket) > 0:
                sent = self.mumble_object.control_socket.send(tcppacket)
                if sent < 0:
                    raise socket.error("Server socket error")
                tcppacket = tcppacket[sent:]
        else:
            self.mumble_object.udp_thread.encrypt_and_send_message(msg)

        self.Log.debug(
            "audio passthrough packet: sequence:{sequence}, type:{type}, length:{len}".format(
                sequence=self.sequence, type=self.codec_type, len=len(payload)
            )
        )

    if len(self._opus_data) == 0 and len(self.pcm) == 0:
        self.queue_empty.set()
    return ()


def _patched_send_audio(orig):
    def send_audio(self):
        if getattr(self, "_opus_data", None):
            _send_opus_audio(self)
        else:
            orig(self)

    return send_audio


def _patched_clear_buffer(orig):
    def clear_buffer(self):
        orig(self)
        _ensure_opus_buffers(self)
        self.lock.acquire()
        self._opus_data = []
        self._opus_durations = []
        self.lock.release()

    return clear_buffer


def _patched_get_buffer_size(orig):
    def get_buffer_size(self):
        base = orig(self)
        _ensure_opus_buffers(self)
        self.lock.acquire()
        opus_seconds = sum(self._opus_durations)
        self.lock.release()
        return base + opus_seconds

    return get_buffer_size


def install_passthrough_send_audio():
    """Monkeypatch pymumble's SendAudio to accept raw Opus frames.

    The patched SendAudio keeps its existing PCM/encode path intact and only
    adds an additional raw-Opus queue for passthrough playback. This avoids
    depending on a modified pymumble install and survives pip reinstalls.
    """
    send_audio_class = sendaudio_module.SendAudio
    if getattr(send_audio_class, "_passthrough_patched", False):
        return
    send_audio_class.add_opus = add_opus
    send_audio_class.clear_buffer = _patched_clear_buffer(
        send_audio_class.clear_buffer
    )
    send_audio_class.get_buffer_size = _patched_get_buffer_size(
        send_audio_class.get_buffer_size
    )
    send_audio_class.send_audio = _patched_send_audio(send_audio_class.send_audio)
    send_audio_class._send_opus_audio = _send_opus_audio
    send_audio_class._passthrough_patched = True