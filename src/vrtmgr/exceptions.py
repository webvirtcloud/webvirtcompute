class FirewallRuleError(Exception):
    """Exception raised for errors in firewall rule operations.

    Attributes:
        msg (str): Explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class IPRedirectError(Exception):
    """Exception raised for errors in IP redirection operations.

    Attributes:
        message (str): Explanation of the error
    """

    def __init__(self, msg):
        self.message = msg
        super().__init__(msg)


class GuestFSError(Exception):
    """Exception raised for errors in GuestFS operations.

    Attributes:
        message (str): Explanation of the error
    """

    def __init__(self, msg):
        self.message = msg
        super().__init__(msg)
