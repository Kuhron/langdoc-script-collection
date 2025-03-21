# Copyright (c) 2023 Wesley Kuhron Jones <wesleykuhronjones@gmail.com> and Ethan Ferrer-Perry
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

import util.WavFiles as wv
import util.AudioOfVideoFiles as av
import util.Correlation as corr
from util.VideoAudioAligningOrganization import get_tmp_dir_path, create_tmp_dir, delete_tmp_dir
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
    # TODO for user interface:
    # - DONE expect directory structure in which all texts have their own dir
    # - and each text dir has one video, one audio, and optionally one .eaf transcript
    # - then the script will create a new video (with offset audio from the audio file)
    # - and if the .eaf is present, it will create an offset .eaf and an offset .srt
    # - pass single text directory path as arg

    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path", type=dir_path,
                        help="the path to the directory where the text's video and audio are stored")
    parser.add_argument(
        "--action", type=str, help="the action to take (TODO figure out how to document this well in docs and/or help str)")
    parser.add_argument("--langs", type=language_list,
                        help="comma-separated list of language codes from InterleavedText.txt.")
    # parser.add_argument("--video", action="store_true", help="create a new video file where the audio is replaced with that from the audio file (and is aligned with the video)")
    # parser.add_argument("--eaf", action="store_true", help="adjust an .eaf transcript to be aligned with the video file")
    # parser.add_argument("--srt", action="store_true", help="TODO")
    # parser.add_argument("--all", action="store_true", help="perform all conversions")
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


    # Note: ASER was recorded on Zoom H5 with no lapel mic in 2021, MAMBU was recorded on Zoom H6 with lapel mic in 2023

    # UNSORTED

    # video_audio_mono_fp, *audio_fps = create_mono_wavs_from_video_file(text_dir, video_fname, audio_prefix, tracks)
    # audio_fnames = [os.path.basename(audio_fp) for audio_fp in audio_fps]
    # print(f"{audio_fnames = }")

    # audio_path = Path(text_dir) / audio_fnames[0]
    # subtitles_path = Path("/home/kuhron/Horokoi/Transcriptions") / "Sessions2023/MAMBU/SubtitlesHk_Raw.srt"

    # Wesley's old crap, TODO clean up / delete

    # items = os.listdir(parent_dir)
    # items_to_exclude = ["VDSTIMULI", "OBJPSTIMULI", "PE2", "NOTEBOOK"] + [f"E{x}" for x in range(12, 21+1)]
    # items_with_exceptions = ["POT3", "GEYANGO"]  # multiple REC files, TODO fix these later

    # # POT3 is cleanly divided into two recordings, REC1 and REC2, each with video, LR audio, and TR1 audio
    # # GEYANGO is divided into two recordings, and the first has two videos (REC1PART1, REC1PART2) with no time gap between them, and one audio (REC1 LR/TR1), and the second has one video (REC2) and one audio (REC2 LR/TR1)
    # # CHOREGIRL has two videos with some missing time between them (RECPART1, RECPART2), and one audio (REC LR/TR1/TR2)

    # # not going to do POT3 or GEYANGO right now because they don't have transcripts in Paradisec as of 2023-09-07
    # # doing CHOREGIRL manually (wrangling in Python shell and Gedit)

    # # make the new EAF files have same name as the MTS file they are to be used as subtitles for (and are being time-aligned with)

    # for item in items:
    #     print(f"current item: {item}")
    #     if item in items_to_exclude or item in items_with_exceptions:
    #         print("skipping\n")
    #         continue
    #     video_dir = os.path.join(parent_dir, item)

    #     if item == "CHOREGIRL":
    #         rec_names = ["RECPART1", "RECPART2"]
    #     elif item == "POT3" or item == "GEYANGO":
    #         raise NotImplementedError("wrangle these items later once have checked the transcribers' work")
    #     else:
    #         rec_names = ["REC"]

    #     for rec_name in rec_names:
    #         need_to_make_correlation_files = (item != "CHOREGIRL")  # exclude ones I did manual offsets for, such as CHOREGIRL
    #         if need_to_make_correlation_files:
    #             video_fname = f"HK1-{item}-{rec_name}.MTS"
    #             audio_prefix = f"HK1-{item}-{rec_name}"
    #             audio_fps_in_dir_raw = [x for x in os.listdir(video_dir) if x.startswith(audio_prefix) and x.endswith(".WAV")]
    #             tracks = [x.replace(audio_prefix+"_", "").replace(".WAV", "") for x in audio_fps_in_dir_raw]
    #             tracks = [x for x in tracks if x != "LR-Mono"]  # extra audio file if we've already run the mono wav creation function, don't double it up in the list (since create_mono_wavs will think it's another audio track like TR1/TR2 and add it to the list of audio files after already adding it by converting the plain LR fname into LR-Mono, so we'll end up with two LR-Mono in the list)

    #             if item == "TRAP3":
    #                 tracks.remove("TR2")  # blank file from me accidentally leaving the second audio channel on while recording

    #             video_audio_mono_fp, *audio_fps = create_mono_wavs_from_video_file(video_dir, video_fname, audio_prefix, tracks)
    #             audio_fnames = [os.path.basename(audio_fp) for audio_fp in audio_fps]
    #             print(f"{audio_fnames=}")

    #             if all(os.path.exists(get_correlation_fp(audio_fname, video_dir)) for audio_fname in audio_fnames):
    #                 print(f"all correlations already computed for item {item}")
    #             else:
    #                 rms_window_seconds = 0.2
    #                 rms_window_samples = int(round(rms_window_seconds * RATE))

    #                 v_arr = get_array_from_file(video_audio_mono_fp)
    #                 v_arr_rms = sliding_rms(v_arr, rms_window_samples)
    #                 v_len = len(v_arr_rms)

    #                 for audio_fname in audio_fnames:
    #                     make_correlation_file(video_dir, v_arr_rms, audio_fname, rms_window_samples)

    #             best_offset_samples = get_max_correlation_position(audio_fnames, video_dir)
    #             print(f"{best_offset_samples = }")
    #             print()

    #             if best_offset_samples is None:
    #                 input("check")

    #             # TODO make new .eaf with edited time refs (in milliseconds)
    #             new_eaf_fname = video_fname.replace(".MTS", ".eaf")
    #             new_eaf_fp = os.path.join(video_dir, new_eaf_fname)
    #             existing_eaf_fname = f"HK1-{item}-TRANSCRIPT.eaf"
    #             existing_eaf_fp = os.path.join(video_dir, existing_eaf_fname)
    #             if not os.path.exists(existing_eaf_fp):
    #                 print(f"item {item} is not transcribed yet; skipping\n")
    #             else:
    #                 create_shifted_eaf_file(existing_eaf_fp, new_eaf_fp, best_offset_samples, allow_overwrite=True)

    #         # make SRT subtitle file based on the new EAF, then watch the video together with subtitles in VLC (I could use MoviePy to make a new video that has the subtitles on it, but don't feel like messing with that just for spot-checking)
    #         # spot check EVERY video to make sure it's aligned
