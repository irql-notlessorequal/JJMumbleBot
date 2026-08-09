import audioop
import os
import select
from time import sleep, time
from JJMumbleBot.lib.utils.print_utils import PrintMode
from JJMumbleBot.lib.utils.logging_utils import log
from JJMumbleBot.settings import global_settings
from JJMumbleBot.lib.resources.strings import *
from JJMumbleBot.lib.utils import runtime_utils as rutils
from JJMumbleBot.lib.errors import AudioError
from threading import Thread
import subprocess as sp
from enum import Enum


class AudioLibrary(Enum):
    FFMPEG = "ffmpeg"


def create_audio_instance(uri: str, audio_lib, skipto: int = 0):
    if audio_lib.value == AudioLibrary.FFMPEG.value:
        audio_lib_path = global_settings.cfg[C_MEDIA_SETTINGS][P_MEDIA_FFMPEG_PATH]
    else:
        raise AudioError(
            "Error: The audio library set for this audio instance is not a valid type!"
        )
    global_settings.audio_thread = Thread(
        target=create_audio_thread,
        args=(
            audio_lib_path,
            audio_lib,
            uri,
            skipto,
            global_settings.cfg.getboolean(
                C_MEDIA_SETTINGS, P_MEDIA_AUDIO_LIB_QUIET, fallback=True
            ),
            global_settings.cfg.getboolean(
                C_MEDIA_SETTINGS, P_MEDIA_USE_STEREO, fallback=True
            ),
        ),
        daemon=True,
    )
    global_settings.audio_thread.start()


def stop_audio_instance():
    if global_settings.audio_inst:
        global_settings.audio_inst.terminate()
        global_settings.audio_inst.kill()
        global_settings.audio_inst = None
    if global_settings.audio_thread:
        global_settings.audio_thread.join()
        global_settings.audio_thread = None


def create_audio_thread(
    audio_lib_path: str,
    audio_lib_type,
    uri: str,
    skipto: int = 0,
    quiet: bool = True,
    stereo: bool = True,
):
    if uri == "":
        return

    global_settings.mumble_inst.send_audio.clear_buffer()
    if global_settings.audio_inst:
        pid = global_settings.audio_inst.pid
        global_settings.audio_inst.terminate()
        try:
            os.kill(pid, 0)
            global_settings.audio_inst.kill()
        except OSError as e:
            log(
                WARNING,
                f"Encountered an error closing the media library process: {e}",
                origin=L_GENERAL,
                error_type=GEN_PROCESS_WARN,
                print_mode=PrintMode.VERBOSE_PRINT.value,
            )
        global_settings.audio_inst = None

    if audio_lib_type.value == AudioLibrary.FFMPEG.value:
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
        params.extend(
            [
                "-nostdin",
                "-i",
                uri,
                "-ss",
                f"{skipto}",
                "-acodec",
                "pcm_s16le",
                "-f",
                "s16le",
                "-ab",
                "192k",
            ]
        )
        if stereo:
            params.extend(["-ac", "2", "-ar", "48000", "-threads", "8", "-"])
        else:
            params.extend(["-ac", "1", "-ar", "48000", "-threads", "8", "-"])
    else:
        return

    log(
        INFO,
        f"Initializing audio playback with command: {' '.join(params)}",
        origin=L_GENERAL,
        print_mode=PrintMode.VERBOSE_PRINT.value,
    )

    audio_proc = sp.Popen(params, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=1024)
    global_settings.audio_inst = audio_proc

    # Capture the media library's stderr in the background so that failures can
    # be surfaced and logged instead of failing silently.
    stderr_lines = []

    def read_stderr():
        for line in audio_proc.stderr:
            stderr_lines.append(line.decode("utf-8", errors="replace").rstrip())

    stderr_thread = Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

    # Diagnostics: log the bot's channel and mute state at playback start, then
    # force-unmute so the server is guaranteed to relay audio even if the local
    # mute flag has drifted out of sync.
    try:
        myself = global_settings.mumble_inst.users.myself
        channel = global_settings.mumble_inst.channels[myself.get("channel_id", 0)]
        log(
            INFO,
            f"Playback start: channel=[{channel.get('name', '?')}({myself.get('channel_id', '?')})], "
            f"self_mute={myself.get('self_mute', 'n/a')}, "
            f"self_deaf={myself.get('self_deaf', 'n/a')}, "
            f"mute={myself.get('mute', 'n/a')}, deaf={myself.get('deaf', 'n/a')}, "
            f"force_tcp_only={global_settings.mumble_inst.force_tcp_only}",
            origin=L_GENERAL,
            print_mode=PrintMode.REG_PRINT.value,
        )
    except Exception as e:
        log(
            WARNING,
            f"Failed to gather playback diagnostics: {e}",
            origin=L_GENERAL,
            print_mode=PrintMode.VERBOSE_PRINT.value,
        )
    unmute_sent = rutils.unmute(force=True)
    log(
        INFO,
        f"Playback start: unmute sent={unmute_sent}",
        origin=L_GENERAL,
        print_mode=PrintMode.VERBOSE_PRINT.value,
    )

    # Re-apply the outgoing audio bandwidth cap so reconnects (which re-read the
    # server's max_bandwidth) cannot push the encoder past the voice packet size limit.
    max_bitrate = global_settings.cfg.getint(
        C_MEDIA_SETTINGS, P_MAX_AUDIO_BITRATE, fallback=128000
    )
    global_settings.mumble_inst.set_bandwidth(max_bitrate)

    def log_audio_error(context):
        stderr_output = "\n".join(stderr_lines) if stderr_lines else "(no error output)"
        log(
            ERROR,
            f"The media library {context}.\nCommand: {' '.join(params)}\n{stderr_output}",
            origin=L_GENERAL,
            error_type=GEN_PROCESS_ERR,
            print_mode=PrintMode.REG_PRINT.value,
        )
        try:
            global_settings.gui_service.quick_gui(
                f"The media library {context}. Check the bot logs for details.",
                text_type="header",
                box_align="left",
            )
        except Exception:
            pass

    buffer_min = (
        0.1  # keep this value low or audio will cut out at the end of the track
    )
    buffer_read_size = 1024
    first_byte_timeout = 8.0
    status_log_interval = 5.0
    stdout_fd = audio_proc.stdout.fileno()
    received_audio = False
    total_bytes = 0
    start_time = time()
    last_status_time = start_time

    def log_status():
        nonlocal last_status_time
        if time() - last_status_time < status_log_interval:
            return
        last_status_time = time()
        log(
            INFO,
            f"Audio playback status: bytes_read={total_bytes}, "
            f"send_buffer={global_settings.mumble_inst.send_audio.get_buffer_size():.3f}s, "
            f"process_alive={audio_proc.poll() is None}",
            origin=L_GENERAL,
            print_mode=PrintMode.VERBOSE_PRINT.value,
        )

    while (
        not global_settings.aud_interface.exit_flag
        and global_settings.audio_inst is audio_proc
    ):
        while (
            global_settings.mumble_inst.send_audio.get_buffer_size() > buffer_min
            and not global_settings.aud_interface.exit_flag
        ):
            sleep(0.01)
            log_status()
        if global_settings.audio_inst is not audio_proc:
            break
        readable, _, _ = select.select([stdout_fd], [], [], 1.0)
        if stdout_fd in readable:
            raw_music = os.read(stdout_fd, buffer_read_size)
            if raw_music:
                received_audio = True
                total_bytes += len(raw_music)
                if global_settings.aud_interface.status.is_playing():
                    global_settings.mumble_inst.send_audio.add_sound(
                        audioop.mul(
                            raw_music,
                            2,
                            global_settings.aud_interface.status.get_volume(),
                        )
                    )
                else:
                    break
            else:
                break
        else:
            if audio_proc.poll() is not None:
                break
            if not received_audio and time() - start_time > first_byte_timeout:
                break
        log_status()

    if audio_proc.poll() is None:
        audio_proc.terminate()
        audio_proc.kill()
    audio_proc.wait()
    stderr_thread.join(timeout=2)

    stopped_externally = global_settings.audio_inst is not audio_proc

    log(
        INFO,
        f"Audio playback ended: bytes_read={total_bytes}, received_audio={received_audio}, "
        f"exit_code={audio_proc.returncode}, stopped_externally={stopped_externally}",
        origin=L_GENERAL,
        print_mode=PrintMode.VERBOSE_PRINT.value,
    )

    if not received_audio and not stopped_externally:
        log_audio_error(
            f"failed to produce any audio output (exit code: {audio_proc.returncode})"
        )

    if stopped_externally or global_settings.aud_interface.exit_flag:
        return

    if global_settings.aud_interface.next_track():
        sleep(0.05)
        create_audio_thread(
            audio_lib_path=audio_lib_path,
            audio_lib_type=audio_lib_type,
            uri=global_settings.aud_interface.status.get_track().uri,
            skipto=0,
            quiet=quiet,
            stereo=stereo,
        )
    else:
        global_settings.aud_interface.reset()
    return
