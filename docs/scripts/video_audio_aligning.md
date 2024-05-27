---
tags:
    - audio
    - wav
    - video
---
# Measure time misalignment in the audio from video camera versus audio recorder
Author: Wesley Kuhron Jones

This script uses correlation between two audio files to measure the amount of time that one is offset from the other. One audio stream is extracted from a video file (MTS, e.g. from the Canon XA11), and the other is taken from an audio file (WAV, e.g. from the Zoom H5 or H6).

The time offset found from this script can then be used in other scripts to edit the timestamps in transcripts and subtitles.

## Setup
Edit the variables in the area at the top of the script labeled "PARAMS TO BE SET BY USER".

Requirements:

```shell
pip install numpy matplotlib
```

## Execution
```shell
python video_audio_aligning.py
```

## Source
```python
{%
   include-markdown '../../video_audio_aligning.py'
   rewrite-relative-urls=false
   comments=false
%}
```
