from pathlib import Path
from ..video import Video


# TODO: extensive tests with parameters, alternative naming, etc
def test_download_video():
    v = Video(video_id="EngW7tLk6R8")
    v.filepath.unlink()
