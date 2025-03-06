# functions having to do with accessing/manipulating the audio of a video file

import os
from pathlib import Path
import moviepy
from numbers import Number

from util.WavFiles import stereo_wav_to_mono, MOVIEPY_AUDIO_EXTENSION_TO_WRITE, MOVIEPY_AUDIO_CODEC
from util.VideoAudioAligningOrganization import get_tmp_dir_path



def get_tmp_fp_for_audio_from_video(video_fp: Path) -> Path:
    text_dir = video_fp.parent
    tmp_dir = get_tmp_dir_path(text_dir)
    v_fname = video_fp.name
    audio_from_video_fname = v_fname + "_AudioFromVideo" + MOVIEPY_AUDIO_EXTENSION_TO_WRITE
    audio_from_video_fp = tmp_dir / audio_from_video_fname
    return audio_from_video_fp


def write_audio_from_video_to_new_audio_file(video_fp: Path, output_audio_fp: Path) -> None:
    if os.path.exists(output_audio_fp):
        print(f"audio file from video already exists, skipping; {output_audio_fp}")
    else:
        
        video = moviepy.VideoFileClip(video_fp)
        video.audio.write_audiofile(output_audio_fp, codec=MOVIEPY_AUDIO_CODEC)
        print(f"audio from {video_fp} written to {output_audio_fp}")


def create_mono_wavs_from_video_file(video_dir, video_fname, audio_prefix, tracks):
    input("don't")
        
    video_audio_mono_fp = stereo_wav_to_mono(video_audio_fp)
    audio_fps = [video_audio_mono_fp]
    if "LR" in tracks:
        lr_fp = os.path.join(video_dir, f"{audio_prefix}_LR.WAV")
        lr_mono_fp = stereo_wav_to_mono(lr_fp)
        audio_fps.append(lr_mono_fp)
    for x in tracks:
        if x not in ["LR", "LR-Mono"]:
            audio_fps.append(os.path.join(video_dir, f"{audio_prefix}_{x}.WAV"))
    assert len(audio_fps) == len(tracks) + 1
    return audio_fps


def replace_audio_in_video_clip(video_path:Path, audio_path:Path, offset_s:Number) -> moviepy.VideoFileClip:
    print(f"combining\nvideo: {video_path}\naudio: {audio_path}\n")

    video = moviepy.VideoFileClip(video_path)
    audio = moviepy.AudioFileClip(audio_path)
    new_video = video.with_audio(moviepy.CompositeAudioClip([audio.with_start(offset_s)]))
    return new_video
