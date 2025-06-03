# Copyright (c) 2025 Wesley Kuhron Jones <wesleykuhronjones@gmail.com> and Ethan Ferrer-Perry
# Licensed under the MIT License:

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from warnings import warn
import argparse
from pathlib import Path

from util.VideoAudioAligningOrganization import get_tmp_dir_path, create_tmp_dir
from util.VideoEditing import create_new_video_file_with_aligned_audio
from util.Eaf import create_shifted_eaf_file_from_text_dir, create_interleaved_text_file_from_eaf
from util.Subtitles import create_srt_file_for_languages
from util.FileTypeDetection import DEFAULT_AUDIO_EXTENSION, DEFAULT_VIDEO_EXTENSION



def dir_path(path_str: str):
    path = Path(path_str).resolve()  # enforce absolute path
    if path.is_dir():
        return path
    raise argparse.ArgumentTypeError(
        f"{path} not valid, should be a directory")


def language_list(s: str):
    return s.split(',')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path", type=dir_path,
                        help="the path to the directory where the text's video and audio are stored")
    parser.add_argument(
        "--action", type=str, help="the action to take (see docs)")
    parser.add_argument("--langs", type=language_list,
                        help="comma-separated list of language codes from the interleaved text file")
    args = parser.parse_args()

    text_name = args.dir_path.stem
    action = args.action

    text_dir = args.dir_path
    if not text_dir.is_absolute():
        warn("text dir is not absolute path")

    tmp_dir_path = get_tmp_dir_path(args.dir_path)
    create_tmp_dir(tmp_dir_path)

    audio_ext = DEFAULT_AUDIO_EXTENSION
    video_ext = DEFAULT_VIDEO_EXTENSION
    eaf_ext = ".eaf"
    subtitle_ext = ".srt"

    action_functions = {
        "video": lambda: create_new_video_file_with_aligned_audio(text_dir, tmp_dir_path, audio_ext, video_ext),
        "eaf": lambda: create_shifted_eaf_file_from_text_dir(text_dir),
        "txt": lambda: create_interleaved_text_file_from_eaf(text_dir),
        "srt": lambda: create_srt_file_for_languages(text_dir, args.langs),
    }

    # there might be a cleaner way to create co-occurrence restrictions on the args, but do it simply until-and-if it gets more complex
    if args.langs is not None and args.action != "srt":
        raise Exception("should only pass --langs flag with --action=srt")

    if args.action is None:
        raise Exception("expected --action flag")

    try:
        f = action_functions[args.action]
    except KeyError:
        raise Exception(f"unknown action {args.action!r}")
    f()
