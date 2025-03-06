import shutil
from pathlib import Path

from util.CliUtil import confirm_action



def get_tmp_dir_path(text_dir: Path):
    # assume we are dealing with only one video and potentially multiple audios, so we will name the temp dir after the video file
    return text_dir / ".tmp"


def create_tmp_dir(tmp_dir_path):
    print(f"temporary files will be stored in {tmp_dir_path}")
    tmp_dir_path.mkdir(exist_ok=True)


def delete_tmp_dir(tmp_dir_path):
    if confirm_action(f"the temporary files in {tmp_dir_path} will be removed"):
        shutil.rmtree(tmp_dir_path)  # be careful to put the right path here!
        print("temporary files have been removed")
    else:
        print("temporary files dir was not removed")
