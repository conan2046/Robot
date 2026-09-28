#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 tools/extract_video_stills.py "$@"
