# -*- coding utf-8 -*-

"""
XTBApi.exceptions
~~~~~~~

Exception module
"""

import logging

LOGGER = logging.getLogger("XTBApi.exceptions")


class CommandFailed(Exception):
    """when a command fail"""

    def __init__(self, response):
        self.msg = "Command failed: " + str(response["errorDescr"])
        self.err_code = response["errorCode"]
        super().__init__(self.msg)


class NotLogged(Exception):
    """when not logged"""

    def __init__(self):
        self.msg = "Not logged, please log in"
        # LOGGER.exception(self.msg)
        super().__init__(self.msg)


class SocketError(Exception):
    """when socket is already closed
    may be the case of server internal error"""

    def __init__(self, msg=""):
        self.msg = "SocketError, mey be an internal error"
        if msg:
            self.msg = msg
        # LOGGER.error(self.msg)
        super().__init__(self.msg)


class TransactionRejected(Exception):
    """transaction rejected error"""

    def __init__(self, message):
        self.msg = "Transaction rejected: {}".format(message)
        # LOGGER.error(self.msg)
        super().__init__(self.msg)
