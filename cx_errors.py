class CxError(Exception):
    """Base class for cx-related errors."""
    def __init__(self, errtype, message, line=0, col=0, severity="error"):
        self.errtype = errtype
        self.message = message
        self.line = line
        self.col = col
        self.severity = severity
        super().__init__(f"{errtype} at {line}:{col}: {message}")

    def to_dict(self):
        return {
            "errtype": self.errtype,
            "message": self.message,
            "line": self.line,
            "col": self.col,
            "severity": self.severity
        }

class CxTokenizationError(CxError):
    pass

class CxParseError(CxError):
    pass

class CxUnsupportedSyntaxError(CxError):
    pass
