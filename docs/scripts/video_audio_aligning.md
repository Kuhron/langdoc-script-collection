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

Setup on Windows 11 (64-bit)
- install Python
- install Git
- cd into your home directory in Powershell
- clone the langdoc-script-collection repo
-- in Powershell:
```shell
git clone https://github.com/Kuhron/langdoc-script-collection
```

- switch to video-audio-aligning branch: 
```shell
git checkout video-audio-aligning
```
- make a virtual environment for installing the required Python packages: 
```shell
python -m venv ../.venvs/video-audio-aligning
```

- activate the virtual env:
```shell
../.venvs/video-audio-aligning/Scripts/activate
```

- if get error:
```shell
File C:\Users\{username}\.venvs\video-audio-aligning\Scripts\Activate.ps1 cannot be loaded because running
scripts is disabled on this system. For more information, see about_Execution_Policies at https:/go.microsoft.com/fwlink/?LinkID=135170.
```

- then you need to enable running unsigned scripts in Powershell so that you can activate the venv. Close the terminal and reopen it with "Run as administrator", then run: 
```shell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted -Force;
```
- then go back into the langdoc-script-collection directory and try activating the venv again

- once the venv is activated, you should see a green "(video-audio-aligning)" prefix on your command prompt
- install the required Python package dependencies:
```shell
python -m pip install -r requirements.txt
```

## Execution
For the script to run properly, the files related to a single text need to be in a directory together. The script expects a single video file (.MTS format), and a single audio file (.WAV format). If either of these are missing, or if there are more than one of these types of files, then it will error.

For the following shell commands, the directory path where this text's files are stored will be referred to as `TEXT_DIR`.

Minor note: The script will create a temporary directory called `.tmp`, where the correlation statistics and temporary media files (such as the audio that was stripped off of the video file) are stored. This can be removed once you are done using the script, and the script can re-compute it anytime as needed.

- TODO WKJ: make steps of workflow more clear and user-friendly here, move mention of viewing help and other unimportant commands to the end/later, mostly want them to know how to enter the directory path, can show example Powershell command series
"C:\Users\emmam\OneDrive\Desktop\Brisi Hedu"  # has space in filepath, needs quotes
- TODO stop asking user to remove temp files, just remove the temp audio ourselves automatically


### Viewing help

```shell
# view help
python video_audio_aligning.py -h
python video_audio_aligning.py --help
```

### Action: creating video with audio replaced and aligned to video timing

```shell
# find correlations between audio from video file and that from .WAV file, and create new video with audio replaced and aligned
python video_audio_aligning.py TEXT_DIR --action=video
```

### Action: creating .eaf transcript that is aligned with video timing

If you want to make subtitles and/or adjust the timestamps on an .eaf transcript, you will also need a single .eaf file in the directory.

```shell
python video_audio_aligning.py TEXT_DIR --action=eaf
```

### Action: creating interleaved text file

For making subtitles for the video, you will need an aligned .eaf transcript (made using `--action=eaf` described above), then you will need to create `InterleavedText.txt` using `--action=txt`.

```shell
python video_audio_aligning.py TEXT_DIR --action=txt
```

Now that `InterleavedText.txt` has been created, open it in a text editor in order to clean up the transcription (text in the target language) and translation (text in the contact language) for subtitles. You can also add new languages if you want to translate the text into them.

`InterleavedText.txt` is organized into sections that are numbered and separated by `----`. Each of these is one segment of the .eaf transcript. Each of them has multiple labeled rows, for different translations. A partial example output from running the script with `--action=txt` is below:

```shell
----
21.
TranscriptionRaw: Marepo tf Singepe ekera komu yaka para ekhamu yoma kere
TranscriptionCleaned: Marepo tf Singepe ekera komu yaka para ekhamu yoma kere
TranslationRaw: Marepo kam daun long kisim Singepe
TranslationCleaned: Marepo kam daun long kisim Singepe
----
22.
TranscriptionRaw: hita tf weipu wemakipu nge ngu Marepo imisi yomakine hita wepuna
TranscriptionCleaned: hita tf weipu wemakipu nge ngu Marepo imisi yomakine hita wepuna
TranslationRaw: mila go yet long namel rot na Marepo kam bungim mipla
TranslationCleaned: mila go yet long namel rot na Marepo kam bungim mipla
----
23.
TranscriptionRaw: harawohe
TranscriptionCleaned: harawohe
TranslationRaw:  bung na
TranslationCleaned:  bung na
----
```

The script created two copies of each transcription and translation line for you, so you can keep the raw/unedited one for reference while you work on cleaning up the text and translating it into any other languages.

The transcription language here is Hurukui, which I like to abbreviate as "Hk", and the transcription language is Tok Pisin (TP). So I go through `InterleavedText.txt` and manually edit the `TranscriptionCleaned` and `TranslationCleaned` rows (replacing these labels with "Hk" and "TP" when I'm done cleaning them), and I add an `Eng` row where I manually type an English translation. The result looks like this:

```shell
----
21.
TranscriptionRaw: Marepo tf Singepe ekera komu yaka para ekhamu yoma kere
Hk: Marepo, Singepe ékera komu yaka para ekhamu yomakere
TranslationRaw: Marepo kam daun long kisim Singepe
TP: Marepo kam daun long kisim Singepe
Eng: Marepo came down to get Singepe
----
22.
TranscriptionRaw: hita tf weipu wemakipu nge ngu Marepo imisi yomakine hita wepuna
Hk: hita wepu wemakepu nge ngu, Marepo imisi yomakine hita wepuna
TranslationRaw: mila go yet long namel rot na Marepo kam bungim mipela
TP: mipela go yet long namel rot na Marepo kam bungim mipla
Eng: we were still en route when we ran into Marepo
----
23.
TranscriptionRaw: harawohe
Hk: harawohe
TranslationRaw:  bung na
TP: bung na
Eng: we met, and
----
```

Now it is ready for running the script with `--action=srt` to create subtitle files based on the cleaned-up and newly translated line texts.

### Action: creating subtitle files

You can create a subtitle file for a single language or multiple languages to be shown at once. I like to have the following:

- one for Hurukui only (labeled as Hiri Motu on YouTube)
- one for Tok Pisin only (labeled as Tok Pisin on YouTube)
- one for English only (labeled as English on YouTube)
- one for Hurukui plus Tok Pisin (labeled as Tamil on YouTube)
- one for Hurukui plus English (labeled as Estonian on YouTube)

The `.srt` subtitle format used by YouTube does not have any metadata about what language the file is in, it just has text and times. So when you upload it you have to tell YouTube what language it should be labeled as.

To create the files, run commands like these:

For one language:
```shell
# expects rows labeled "Hk:" in InterleavedText.txt
python video_audio_aligning.py TEXT_DIR --action=srt --langs=Hk
```

This creates a new subtitle file called `Subtitles_Hk.srt`.

For multiple languages:
```shell
# expects rows labeled "Hk:" and "Eng:" in InterleavedText.txt
python video_audio_aligning.py TEXT_DIR --action=srt --langs=Hk,Eng
```

This creates a new subtitle file called `Subtitles_Hk_Eng.srt`.

The script does not care if there are other row labels present in `InterleavedText.txt` besides the ones you are making into a subtitle file, so you can use the same `InterleavedText.txt` with all of your languages even if you are only making .srt files for one or a few of the languages.

## Troubleshooting

If pip installation fails, use the appropriate command below to install each dependency one at a time:

```shell
cat requirements.txt | xargs -n 1 python -m pip install  # on Linux or Mac

foreach($line in Get-Content requirements.txt) {python -m pip install $line}  # on Windows Powershell

FOR /F %k in (requirements.txt) DO pip install %k  # on Windows cmd
```
If none of these work, see [here](https://stackoverflow.com/questions/22250483/stop-pip-from-failing-on-single-package-when-installing-with-requirements-txt) for more possible commands to run.

The following warning can be ignored:
`RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work`

If Python complains that you cannot install the `audioop` package because it is deprecated, use pip to install the long-term support version:
```shell
python -m pip install audioop-lts
```

If the script runs but then crashes with "ModuleNotFoundError: No module named 'pyaudioop'":
```shell
python -m pip install audioop-lts
```

If the script complains that your directory where you stored the files (`TEXT_DIR`) is not a directory and you are on Windows, it might be because that directory is a OneDrive link. Try copying the files into a directory that is stored locally on your computer or on an external hard drive, and not a OneDrive link.

If the resulting .MTS video does not play in your default media player, try playing it in VLC Media Player.


## Source
```python
{%
   include-markdown '../../video_audio_aligning.py'
   rewrite-relative-urls=false
   comments=false
%}
```
