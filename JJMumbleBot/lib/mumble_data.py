class MumbleData:
    ip_address = None
    port = 0
    user_id = None
    password = None
    certificate = None
    stereo = False
    debug = False
    force_tcp_only = True

    def __init__(self, ip: str, port: int, uid: str, pwd: str, cert: str, stereo: bool, reconnect: bool, debug: bool = False, force_tcp_only: bool = True):
        self.ip_address = ip
        self.port = port
        self.user_id = uid
        self.password = pwd
        self.certificate = cert
        self.stereo = stereo
        self.auto_reconnect = reconnect
        self.debug = debug
        self.force_tcp_only = force_tcp_only
