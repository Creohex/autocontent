class Error(Exception):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg)


class ValidationError(Error):
    def __init__(self, msg: str = None, value: str = None) -> None:
        super().__init__(msg=msg or f"Invalid value {value}")


class InvalidFileName(Error):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg=msg or "Invalid file name")


class InvalidFilePath(Error):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg=msg or "Invalid file path")


class VideoException(Error):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg)


class VideoUnavailable(VideoException):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg=msg or "Video unavailable")
