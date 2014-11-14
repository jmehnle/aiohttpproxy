class Error(Exception):
    def __init__(self, message = None, original_exception = None, exception_location = None):
        StandardError.__init__(self)
        self.message            = message
        self.original_exception = original_exception
        self.filename, self.lineno, self.scope, self.line = exception_location \
            if exception_location \
            else (None, None, None, None)

class OptionsError(Error): pass  # Options error.

# vim:sw=4 sts=4
