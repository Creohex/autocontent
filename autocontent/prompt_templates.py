

VIDEO_TITLE_GENERATION = """\
TEXT is a video file transcription.
Generate {{title_count}} titles for provided TEXT.
Output format must be a list of strings, like this:
["title1", "title2", "title3"]

TEXT: {{context}}
"""


BEST_TITLE = """\
TITLES is a list of strings containing titles for a (short) youtube video.
TEXT is a transcription of a video file.
Pick and return a TITLE that best suits TEXT and will hopefully result in higher viewer conversion.
Output must be a single title (sentence).

TITLES: {{titles}}
TEXT: {{context}}
"""
