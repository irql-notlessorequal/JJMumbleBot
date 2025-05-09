###########################################################################
# INTERNAL STRING CONSTANTS - DO NOT MODIFY
ENV_MUMBLE_IP = "MUMBLE_IP"
ENV_MUMBLE_PORT = "MUMBLE_PORT"
ENV_MUMBLE_PASSWORD = "MUMBLE_PASSWORD"
# PROGRAM CONFIG CATEGORY STRINGS
C_CONNECTION_SETTINGS = "Connection Settings"
C_MAIN_SETTINGS = "Main Settings"
C_PLUGIN_SETTINGS = "Plugin Settings"
C_PGUI_SETTINGS = "PGUI Settings"
C_MEDIA_SETTINGS = "Media Settings"
C_LOGGING = "Logging"
# PROGRAM CONFIG PARAMETER STRINGS
# Connection Settings
P_USER_ID = "UserID"
P_USER_CERT = "UserCertification"
P_SERVER_RECONNECT = "AutoReconnect"
P_DEFAULT_CHANNEL = "DefaultChannel"
P_DEFAULT_SU = "DefaultSuperUser"
P_SELF_REGISTER = "SelfRegister"
P_USER_COMMENT = "DefaultComment"
# Main Settings
P_DB_INTEGRITY = "EnableDatabaseIntegrityCheck"
P_DB_BACKUP = "EnableDatabaseBackup"
P_CMD_TICK_RATE = "CommandTickRate"
P_CMD_MULTI_LIM = "MultiCommandLimit"
P_CMD_TOKEN = "CommandToken"
P_CMD_QUEUE_LIM = "CommandQueueLimit"
P_CMD_HIST_LIM = "CommandHistoryLimit"
# Media Settings
P_MEDIA_FFMPEG_PATH = "FfmpegPath"
P_MEDIA_VLC_PATH = "VlcPath"
P_MEDIA_USE_STEREO = "UseStereoAudio"
P_MEDIA_AUDIO_LIB_QUIET = "AudioLibraryRunQuiet"
P_MEDIA_DEFAULT_VOLUME = "DefaultVolume"
P_MEDIA_DUCK_AUDIO = "UseAudioDuck"
P_MEDIA_DUCK_VOLUME = "DuckingVolume"
P_MEDIA_DUCK_THRESHOLD = "DuckingThreshold"
P_MEDIA_DUCK_START_DELAY = "DuckingStartDelay"
P_MEDIA_DUCK_END_DELAY = "DuckingEndDelay"
P_MEDIA_QUEUE_LEN = "MaxQueueLength"
P_MEDIA_PROXY_URL = "YoutubeDLProxyURL"
P_MEDIA_COOKIE_FILE = "YoutubeDLCookieFile"
P_MEDIA_PLAYER_BACKEND = "YoutubeDLPlayerBackend"
P_MEDIA_POT_URL = "YoutubeDLPOTBackend"
P_PERM_MEDIA_DIR = "PermanentMediaDirectory"
P_TEMP_MED_DIR = "TemporaryMediaDirectory"
# PGUI Settings
P_CANVAS_BG_COL = "CanvasBGColor"
P_CANVAS_IMG_BG_COL = "CanvasImageBGColor"
P_CANVAS_ALGN = "CanvasAlignment"
P_CANVAS_BORD = "CanvasBorder"
P_CANVAS_TXT_COL = "CanvasTextColor"
P_TXT_DEFAULT_FONT = "DefaultFont"
P_TXT_HEAD_COL = "HeaderTextColor"
P_TXT_IND_COL = "IndexTextColor"
P_TXT_SUBHEAD_COL = "SubHeaderTextColor"
# Plugin Settings
P_PLUG_DISABLED = "DisabledPlugins"
P_PLUG_SAFE = "SafeModePlugins"
P_PLUG_ALLOWED_CHANNELS = "AllowedRootChannelsForTempChannels"
# Logging
P_LOG_ENABLE = "EnableLogging"
P_LOG_MAX = "MaxLogs"
P_LOG_SIZE_MAX = "MaxLogSize"
P_LOG_MESSAGES = "HideMessageLogging"
P_LOG_DIR = "LogDirectory"
P_LOG_TRACE = "LogStackTrace"
###########################################################################
# LOGGING STRINGS - DO NOT MODIFY
INFO = "info"
DEBUG = "debug"
WARNING = "warning"
ERROR = "error"
CRITICAL = "critical"

# EXTERNAL LINKS - DO NOT MODIFY
LINK_WIKI = "https://duckboss.github.io/JJMumbleBot/wiki/new/whats_new.html"

# TEMPORARY DATA STRINGS - DO NOT MODIFY
T_TEMP_IMG_NAME = "_image"
T_TEMP_CMD_PERMISSIONS = "_permissions"
T_TEMP_USER_PRIVILEGES = "_privileges"
T_TEMP_ALIASES = "_aliases"

# ERROR STRINGS - DO NOT MODIFY
CMD_INVALID_ERR = "InvalidCommandFormat"
CMD_PROCESS_ERR = "CommandProcessingError"
GEN_PROCESS_ERR = "GeneralProcessingError"
DEP_PROCESS_ERR = "DependencyProcessingError"
# WARNING STRINGS - DO NOT MODIFY
GEN_PROCESS_WARN = "GeneralProcessingWarning"
DEP_PROCESS_WARN = "DependencyProcessingWarning"
WARN_INVALID_IMG_FORMAT = "InvalidImageFormat"
WARN_FIXED_IMG_FORMAT = "FixedImageFormat"
###########################################################################
# LOGGING PREFIX STRINGS
L_GENERAL = "General"
L_USER_PRIV = "UserPrivileges"
L_DATABASE = "Database"
L_COMMAND = "Command"
L_STARTUP = "StartUp"
L_SHUTDOWN = "ShutDown"
L_ALIASES = "Aliases"
L_LOGGING = "Logging"
L_DEPENDENCIES = "Dependencies"
L_WEB_INTERFACE = "WebInterface"
L_PLUGIN = "Plugin"
###########################################################################
# PLUGIN CONFIG CATEGORY STRINGS
C_PLUGIN_INFO = "Plugin Information"
C_PLUGIN_REQS = "Plugin Requirements"
C_PLUGIN_TYPE = "Plugin Type"
C_PLUGIN_SET = "Plugin Settings"
# PLUGIN CONFIG PARAMETER STRINGS
# Plugin Information
P_PLUGIN_VERS = "PluginVersion"
P_PLUGIN_NAME = "PluginName"
P_PLUGIN_DESC = "PluginDescription"
P_PLUGIN_CMDS = "PluginCommands"
P_PLUGIN_LANG = "PluginLanguage"
# Plugin Type
P_CTR_PLUGIN = "ControllablePlugin"
P_AUD_PLUGIN = "AudioPlugin"
P_IMG_PLUGIN = "ImagePlugin"
P_CORE_PLUGIN = "CorePlugin"
P_EXT_PLUGIN = "ExtensionPlugin"
# Universal Plugin Settings
P_THREAD_WAIT = "ThreadWaitForCommands"
P_THREAD_SINGLE = "UseSingleThread"
###########################################################################
# BOT META INFORMATION STRINGS
META_NAME = "JJMumbleBot"
META_VERSION = "5.3.0"
###########################################################################
