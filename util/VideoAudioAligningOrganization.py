import shutil
from pathlib import Path
from warnings import warn
from typing import Tuple

from util.CliUtil import confirm_action


def get_tmp_dir_path(text_dir: Path, create_if_absent=False):
    # assume we are dealing with only one video and potentially multiple audios, so we will name the temp dir after the video file
    path = text_dir / ".tmp"
    if create_if_absent and not path.exists():
        path.mkdir()
    return path


def create_tmp_dir(tmp_dir_path):
    print(f"temporary files will be stored in {tmp_dir_path}")
    tmp_dir_path.mkdir(exist_ok=True)


def delete_tmp_dir(tmp_dir_path):
    if confirm_action(f"Would you like to delete the temporary files in {tmp_dir_path}? This will not delete the aligned .MTS file."):
        shutil.rmtree(tmp_dir_path)  # be careful to put the right path here!
        print("temporary files have been removed")
    else:
        print("temporary files dir was not removed")


def delete_audio_from_tmp_dir(tmp_dir_path, audio_suffix):
    for fp in tmp_dir_path.glob("*" + audio_suffix):
        fp.unlink()
        print(f"deleted temporary audio file: {fp}")


def get_single_audio_and_video_fps_from_text_dir(text_dir: Path, audio_ext: str, video_ext: str) -> Tuple[Path]:
    audio_fps = list(text_dir.glob("*" + audio_ext))
    if len(audio_fps) != 1:
        zero = len(audio_fps) == 0
        error_str = f"there should be exactly one audio file ({audio_ext}) in the directory, but found " + (
            "none" if zero else f"the following {len(audio_fps)}:")
        for fp in audio_fps:
            error_str += str(fp) + "\n"
        raise Exception(error_str)
    video_fps = list(text_dir.glob("*" + video_ext))
    if len(video_fps) != 1:
        zero = len(video_fps) == 0
        error_str = f"there should be exactly one video file ({video_ext}) in the directory, but found " + (
            "none" if zero else f"the following {len(video_fps)}:")
        for fp in video_fps:
            error_str += str(fp) + "\n"
        raise Exception(error_str)

    audio_fp, = audio_fps
    video_fp, = video_fps

    if not audio_fp.is_absolute():
        warn("audio fp is not absolute")
    if not video_fp.is_absolute():
        warn("video fp is not absolute")

    return audio_fp, video_fp
