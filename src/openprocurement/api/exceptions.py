class BaseConfigError(Exception):
    """Base config error class"""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ConfigAliasError(BaseConfigError):
    """Error class for aliases stuff."""
    def __init__(self, msg):
        super(ConfigAliasError, self).__init__(msg)
        self.msg = msg
