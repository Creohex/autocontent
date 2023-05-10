# About
This is a hobby project started mostly due to curiousity of tackling a compound tooling/automation problem and a way to hone skills and practices along the way.

The core idea is to eventually implement an automated pipeline of repurposing existing video content (mainly - podcasts) into complete finished/stylized/coherent shorter bite-sized format.

Overall scope, but it's definitely not final and is subject to change:
- Having the means to extract content - videos, transcriptions, etc.
- Text analysis, chunking, title generation, keyword extraction, ... (OpenAI's GPT, AI-21 or something of that sort)
- Video/subtitle editing, cutting, stylizing, formatting, elimination of quiet parts, etc.
- Speech recognition / subtitle generation
- Computer vision (face position identification - for frame centering)
- Integrations (google trends, openai, youtube api, ...)
- CLI implementation
- Rudimentary GUI
- Other: scheduler (content uploading), queue (source content processing/pipelining), ...

# Preparation / Usage
```bash
poetry install
source .venv/bin/activate
./toolset.py --help
./toolset.py <command> --help
```

Currently it might not be stable, but eventually there are plans to make a proper package out of it and adapt for windows as well.
