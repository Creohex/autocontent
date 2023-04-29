class Error(Exception):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg)


class InvalidFileName(Error):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg="Invalid file name")


class VideoException(Error):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg)


class VideoUnavailable(VideoException):
    def __init__(self, msg: str = None) -> None:
        super().__init__(msg="Video unavailable")
