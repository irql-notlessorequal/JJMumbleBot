server_tools_metadata = None
plugin_name = None
user_connections = {}

# In-memory cache for the yt-dlp update check (timestamp: epoch seconds, versions: str/None).
ytdlp_update_check = {
    "timestamp": 0,
    "installed_version": None,
    "latest_version": None,
}
