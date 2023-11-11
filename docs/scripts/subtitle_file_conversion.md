---
tags:
    - audio
    - wav
---
# TODO update for this script
Author: Wesley Kuhron Jones

This script amplifies segments of a WAV audio file so that it is more audible when played on a laptop or speaker in the field during transcription sessions with language consultants. It has been optimized to use low amounts of RAM so that it can be run on small laptops like the Asus that I use in Papua New Guinea.

Procedure that I follow manually:

- find a section of audio between silent spots (or at least significantly quieter than the voice volume)
- amplify it and go past clipping to some extent, so the average amplitude is enough to hear well
- ignore isolated small spikes that make the max amplitude much larger than the average, I've never had a problem with clipping too much making it hard for consultants to understand, so err on the side of being too loud

This script automates this procedure.

## Setup
Edit the variables in the area at the top of the script labeled "PARAMS TO BE SET BY USER".

Requirements:

```shell
pip install numpy matplotlib
```

## Execution
```shell
python amplify_wav.py
```

## Source
```python
{%
   include-markdown '../../amplify_wav.py'
   rewrite-relative-urls=false
   comments=false
%}
```
