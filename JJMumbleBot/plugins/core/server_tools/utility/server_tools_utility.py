from JJMumbleBot.lib.utils import dir_utils
from JJMumbleBot.plugins.core.server_tools.utility import settings
from JJMumbleBot.lib.utils.logging_utils import log
from JJMumbleBot.lib.resources.strings import ERROR, L_COMMAND, GEN_PROCESS_ERR
from JJMumbleBot.lib.utils.print_utils import PrintMode
from os import path
import csv
import time


# How long (in seconds) the latest yt-dlp version is cached in memory before re-checking.
YTDLP_UPDATE_CACHE_TTL = 24 * 60 * 60


def check_ytdlp_update(force=False):
    """Checks the latest yt-dlp release against the installed version.

    Uses yt-dlp's own update machinery (Updater.query_update) and caches the
    result in memory for YTDLP_UPDATE_CACHE_TTL seconds.
    Returns (installed_version, latest_version) when an update is available,
    None when up-to-date or the check fails.
    """
    now = time.time()
    cached = settings.ytdlp_update_check
    if (
        not force
        and cached["latest_version"] is not None
        and (now - cached["timestamp"]) < YTDLP_UPDATE_CACHE_TTL
    ):
        if cached["installed_version"] != cached["latest_version"]:
            return (cached["installed_version"], cached["latest_version"])
        return None

    try:
        import yt_dlp
        from yt_dlp.update import Updater

        installed_version = yt_dlp.version.__version__
        ydl = yt_dlp.YoutubeDL({"quiet": True})
        update_info = Updater(ydl).query_update()
        latest_version = update_info.version if update_info else installed_version

        cached["timestamp"] = now
        cached["installed_version"] = installed_version
        cached["latest_version"] = latest_version

        if latest_version and latest_version != installed_version:
            return (installed_version, latest_version)
        return None
    except Exception as e:
        log(
            ERROR,
            f"Could not check for yt-dlp updates: {e}",
            origin=L_COMMAND,
            error_type=GEN_PROCESS_ERR,
            print_mode=PrintMode.VERBOSE_PRINT.value,
        )
        return None


def ytdlp_update_message(installed_version, latest_version):
    return (
        f"The installed yt-dlp version ({installed_version}) is out of date! "
        f"The latest version is {latest_version}. "
        f"Update it with: pip install -U yt-dlp"
    )


def read_user_connections():
    try:
        if not path.exists(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/'):
            dir_utils.make_directory(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/')
            create_empty_user_connections()

        with open(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/user_connections.csv', mode='r') as csv_file:
            settings.user_connections = {}
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                settings.user_connections[row['username']] = row['track']
        return True
    except IOError:
        log(ERROR, f"Encountered an error reading/writing the user_connections.csv file.",
            origin=L_COMMAND, error_type=GEN_PROCESS_ERR, print_mode=PrintMode.VERBOSE_PRINT.value)
        return False


def save_user_connections():
    try:
        if not path.exists(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/'):
            dir_utils.make_directory(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/')

        with open(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/user_connections.csv', mode='w') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=['username', 'track'])
            csv_writer.writeheader()
            for user in settings.user_connections:
                csv_writer.writerow({'username': user, 'track': settings.user_connections[user]})
        return True
    except IOError:
        log(ERROR, f"Encountered an error reading/writing the user_connections.csv file.",
            origin=L_COMMAND, error_type=GEN_PROCESS_ERR, print_mode=PrintMode.VERBOSE_PRINT.value)
        return False


def create_empty_user_connections():
    try:
        if not path.exists(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/user_connections.csv'):
            with open(f'{dir_utils.get_plugin_data_dir()}/{settings.plugin_name}/user_connections.csv', mode='w') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=['username', 'track'])
                csv_writer.writeheader()
            settings.user_connections = {}
        return True
    except IOError:
        log(ERROR, f"Encountered an error reading/writing the user_connections.csv file.",
            origin=L_COMMAND, error_type=GEN_PROCESS_ERR, print_mode=PrintMode.VERBOSE_PRINT.value)
        return False
