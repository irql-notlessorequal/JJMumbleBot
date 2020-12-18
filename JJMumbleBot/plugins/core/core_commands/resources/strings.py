from JJMumbleBot.lib.utils.runtime_utils import get_command_token

###########################################################################
# CORE COMMANDS PLUGIN CONFIG PARAMETER STRINGS

# ERROR STRINGS
CMD_INVALID_SET_COMMENT = [
    "ERROR: Incorrect command formatting!",
    f"Format: {get_command_token()}setcomment 'message'"
]
CMD_INVALID_REMOVE_ALIAS = [
    "ERROR: Incorrect command formatting!",
    f"Format: {get_command_token()}removealias 'alias_name'"
]
CMD_INVALID_SET_ALIAS = [
    "ERROR: Incorrect command formatting!",
    f"Format: {get_command_token()}setalias 'alias_name' (cmd) param | (cmd) param | ..."
]