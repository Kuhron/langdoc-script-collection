---
tags:
    - audio
    - wav
    - video
    - mts
    - subtitles
    - srt
    - transcript
    - eaf
---
# Measure time misalignment in the audio from video camera versus audio recorder
Authors: Wesley Kuhron Jones (wesleykuhronjones at g mail), Ethan Ferrer-Perry

This script uses correlation between two audio files to measure the amount of time that one is offset from the other. One audio stream is extracted from a video file (MTS, e.g. from the Canon XA11), and the other is taken from an audio file (WAV, e.g. from the Zoom H5 or H6).

Once this is known, a variety of actions can be taken to streamline the workflow of preparing videos for YouTube.

Actions:

- **video**: create new video where the audio has been replaced with the content of the audio file, which is aligned to match the video's timing
- **eaf**: create a new .eaf transcript file which has the timestamps changed to match the video's timing
- **txt**: create a file called `InterleavedText.txt` which contains the transcriptions and translations from the .eaf transcript, so that the user can edit these to clean them up for subtitle creation
- **srt**: create .srt subtitle files based on the contents of `InterleavedText.txt`; needs `--langs` flag to tell which languages to include in this subtitle file

## Setup
The script is run in the command line, with different actions done by passing arguments and flags.

Requirements:

```shell
# go into the repo's directory
cd langdoc-script-collection

# create virtual environment
python -m venv video-audio-aligning

# activate the virtual environment
source video-audio-aligning/bin/activate  # on Linux
video-audio-aligning/Scripts/activate  # on Windows

# install requirements
python -m pip install -r requirements.txt
```

## Execution
For the script to run properly, the files related to a single text need to be in a directory together. The script expects a single video file (.MTS format), and a single audio file (.WAV format). If either of these are missing, or if there are more than one of these types of files, then it will error.

For the following shell commands, the directory path where this text's files are stored will be referred to as `TEXT_DIR`.

```shell
# view help
python video_audio_aligning.py -h
python video_audio_aligning.py --help

# find correlations between audio from video file and that from .WAV file, and create new video with audio replaced and aligned
python video_audio_aligning.py TEXT_DIR --action=video
```

If you want to make subtitles and/or adjust the timestamps on an .eaf transcript, you will also need a single .eaf file in the directory.

```shell
python video_audio_aligning.py TEXT_DIR --action=eaf
```

For making subtitles for the video, you will need an aligned .eaf transcript (made using `--action=eaf` described above), then you will need to create `InterleavedText.txt` using `--action=txt`.

```shell
python video_audio_aligning.py TEXT_DIR --action=txt
```

Now that `InterleavedText.txt` has been created, open it in a text editor and TODO

```shell
# expects lines labeled "Hk:" and "Eng:" in InterleavedText.txt
python video_audio_aligning.py TEXT_DIR --action=srt --langs=Hk,Eng
```

```shell
# generic usage pattern
python video_audio_aligning.py [-h] [--action ACTION] [--langs LANGS] dir_path
```

The script will create a temporary directory called `.tmp`, where the correlation statistics and temporary media files (such as the audio that was stripped off of the video file) are stored. This can be removed once you are done using the script, and the script can re-compute it anytime as needed.


## Troubleshooting

- TODO write up instructions for non-techy users (how to install git, clone the repo, python, install the requirements, note that newer pythons will need audioop-lts package because audioop was deprecated in 3.13)
- TODO paste error messages so they can Ctrl-F their problem and find the solution as easily as possible

If pip installation fails, use the appropriate command below to install each dependency one at a time:

```shell
cat requirements.txt | xargs -n 1 python -m pip install  # on Linux or Mac

foreach($line in Get-Content requirements.txt) {python -m pip install $line}  # on Windows Powershell

FOR /F %k in (requirements.txt) DO pip install %k  # on Windows cmd
```
If none of these work, see [here](https://stackoverflow.com/questions/22250483/stop-pip-from-failing-on-single-package-when-installing-with-requirements-txt) for more possible commands to run.

The following warning can be ignored:
.\langdoc-script-collection\video-audio-aligning\lib\site-packages\pydub\utils.py:170: RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
  warn("Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work", RuntimeWarning)

If Python complains that you cannot install the `audioop` package because it is deprecated, use pip to install the long-term support version:
```shell
python -m pip install audioop-lts
```

If the script complains that your directory where you stored the files (`TEXT_DIR`) is not a directory and you are on Windows, it might be because that directory is a OneDrive link. If that is the case, then you're hosed because IDFK how to fix it :P **TODO fix**


## Source
```python
{%
   include-markdown '../../video_audio_aligning.py'
   rewrite-relative-urls=false
   comments=false
%}
```
