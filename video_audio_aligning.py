# Copyright (c) 2023 Wesley Kuhron Jones <wesleykuhronjones@gmail.com>
# Licensed under the MIT License, see below


### PARAMS TO BE SET BY USER ###


### END USER PARAMS ###


import os
from warnings import warn
import shutil
import numpy as np
import matplotlib.pyplot as plt
import moviepy
from moviepy.video.tools.subtitles import SubtitlesClip
import sys
import argparse
from pathlib import Path
from numbers import Number

from util.SoundFileStatistics import sliding_rms
import util.WavFiles as wv
import util.AudioOfVideoFiles as av
from util.VideoAudioAligningOrganization import get_tmp_dir_path, create_tmp_dir, delete_tmp_dir



def add_subtitle_to_video_clip(video:moviepy.VideoFileClip, subtitles_path:Path, offset_s:Number) -> moviepy.VideoFileClip:
    # this adds the subtitles to the actual video, not just text subtitles that can be turned on/off, it will actually be on the video images
    # TODO at some point, can move the subtitles into a better position and give text black background, but for now I'll just use YouTube .srt functionality

    font_path = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    generator = lambda txt: moviepy.TextClip(text=txt, font=font_path, font_size=24, color="white")
    subtitles = SubtitlesClip(subtitles_path, make_textclip=generator)
    subtitles = subtitles.with_start(offset_s)
    new_video = moviepy.CompositeVideoClip([video, subtitles])  # without specifying subtitle position, it's just in the upper left corner
    return new_video


def write_video_clip_to_file(video:moviepy.VideoFileClip, video_path:Path) -> None:
    codec = {
        ".MTS": "h264",
    }.get(video_path.suffix)

    video.write_videofile(video_path, codec=codec)
    print(f"wrote new video to {video_path}")


def get_correlation_from_offset(v_arr_rms, a_arr_rms, offset_samples):
    # start audio earlier with negative offset, later with positive offset
    # so since our zero point is both files starting at the same time and potentially ending at different times, when have negative offset we should chop off the front of the audio, and when we have positive offset we should pad the front of the audio
    assert type(offset_samples) is int
    if offset_samples < 0:
        new_a_arr_rms = a_arr_rms[-offset_samples:]
    else:
        new_a_arr_rms = np.concatenate([np.zeros((offset_samples,)), a_arr_rms])
    min_len = min(v_len, len(new_a_arr_rms))
    new_v_arr_rms = v_arr_rms[:min_len]
    new_a_arr_rms = new_a_arr_rms[:min_len]
    corr = np.corrcoef(new_v_arr_rms, new_a_arr_rms)[0,1]
    return corr


def find_correlations_brute_force(v_arr_rms, a_arr_rms, offsets_samples):
    print(f"finding correlations between video and audio")
    offsets_samples_used = []
    correlations = []
    for i, offset_samples in enumerate(offsets_samples):
        print(f"progress: {i+1}/{len(offsets_samples)}", end="\r")
        corr = get_correlation_from_offset(v_arr_rms, a_arr_rms, offset_samples)
        # if corr >= 0.75:
        #     print(f"{offset_samples = }, {corr = :+.6f}\t\t\r")
        offsets_samples_used.append(offset_samples)  # redundant but whatever
        correlations.append(corr)
    print()
    print(f"done finding correlations between video and audio")
    return correlations, offsets_samples_used


def find_correlations_binary_search(v_arr_rms, a_arr_rms, offsets_samples):
    # don't care enough, can do it if need to run this a lot more later
    raise NotImplementedError


def make_correlation_file(video_dir, v_arr_rms, audio_fname, rms_window_samples):
    print(f"making correlation file for {audio_fname = }")
    audio_fp = os.path.join(video_dir, audio_fname)
    corr_fp = get_correlation_fp(audio_fname, video_dir)
    if os.path.exists(corr_fp):
        print(f"file exists, skipping: {corr_fp}")
        return

    # find correlation between it and video audio at various offsets
    offsets_seconds_all = np.arange(-10, 10, 0.1)
    offsets_samples_all = [int(round(wv.RATE * x)) for x in offsets_seconds_all]
    correlations = []
    a_arr = wv.get_array_from_file(audio_fp)
    a_arr_rms = sliding_rms(a_arr, rms_window_samples)

    print(f"{v_arr_rms.shape = }")
    print(f"{a_arr_rms.shape = }")

    # make it so we slide the audio and keep the video in place, since I am making edited .eaf files that will match the video time
    print(f"making correlation")
    correlations, offsets_samples_used = find_correlations_brute_force(v_arr_rms, a_arr_rms, offsets_samples_all)
    # correlations, offsets_samples_used = find_correlations_binary_search(v_arr_rms, a_arr_rms, offsets_samples_all)

    offsets_seconds_used = [x/wv.RATE for x in offsets_samples_used]
    assert len(offsets_samples_used) == len(correlations)
    # plt.plot(offsets_seconds_used, correlations)
    # plt.show()
    with open(corr_fp, "w") as f:
        for i in range(len(offsets_samples_used)):
            f.write(f"{offsets_samples_used[i]}\t{correlations[i]}\n")
    print(f"wrote correlations to {corr_fp}")


def get_correlation_fp(audio_fname, video_dir):
    corr_fname = f"corr_{audio_fname}.txt"
    corr_fp = os.path.join(video_dir, corr_fname)
    return corr_fp


def get_max_correlation_position(audio_fnames, video_dir):
    corr_fps = [get_correlation_fp(audio_fname, video_dir) for audio_fname in audio_fnames]
    discrepancy_tolerance = 0.05 * wv.RATE
    best_offsets = []
    corr_series = []
    for corr_fp in corr_fps:
        with open(corr_fp) as f:
            lines = f.readlines()
        while "" in lines:
            lines.remove("")
        lines_stripped_split = [line.strip().split("\t") for line in lines]
        offsets = []
        this_corr_series = []
        for line in lines_stripped_split:
            offset, corr = line
            offset = int(offset)
            corr = float(corr)
            offsets.append(offset)
            this_corr_series.append(corr)
        
        best_offset = offsets[this_corr_series.index(max(this_corr_series))]  # don't optimize prematurely?
        best_offsets.append(best_offset)
        corr_series.append(this_corr_series)

    # # debug
    # for corr, corr_fp in zip(corr_series, corr_fps):
    #     plt.plot(corr, label=corr_fp)
    # plt.show()

    best_offsets = sorted(set(best_offsets))
    print(f"{best_offsets = }")

    if any(abs(x - min(offsets)) <= discrepancy_tolerance or abs(x - max(offsets)) <= discrepancy_tolerance for x in best_offsets):
            raise Exception(f"Warning: some offsets are too close to min or max offset; you probably need to expand the window of offsets checked; {best_offsets = }")

    if len(best_offsets) == 1:
        return best_offsets[0]
    else:
        if max(best_offsets) - min(best_offsets) > discrepancy_tolerance:
            raise Exception(f"Warning: best offsets are too far apart: {best_offsets}")
        else:
            average_offset = sum(best_offsets) / len(best_offsets)
            return int(round(average_offset))


def create_shifted_eaf_file(existing_eaf_fp, new_eaf_fp, best_offset_samples, allow_overwrite=False):
    # ADD the offset to the eaf times, since the eaf times were for the audio but we're changing it to the video (always or almost always a negative offset since the video was started later so we want earlier timestamps)
    # could parse XML but whatever, the format is simple enough to just do string replacement
    if os.path.exists(new_eaf_fp) and not allow_overwrite:
        raise Exception(f"would overwrite file {new_eaf_fp}")
    best_offset_ms = int(round(best_offset_samples * 1000/44100))  # convert time units!
    with open(existing_eaf_fp) as f:
        lines = f.readlines()
    new_lines = []
    for line_i, l in enumerate(lines):
        assert l.endswith("\n") or line_i == len(lines) - 1, repr(l)  # just so I know whether to do "".join or "\n".join later
        if "TIME_VALUE=" in l:
            i = l.index("TIME_VALUE=") + len("TIME_VALUE_")
            l1, l2 = l[:i], l[i:]
            assert l1.endswith("TIME_VALUE=")
            assert l2[0] == '"'
            assert l2.count('"') == 2
            j = 1 + l2[1:].index('"')
            assert l2[j] == '"'
            n = int(l2[1:j])
            new_n = n + best_offset_ms
            new_n = max(0, new_n)
            new_l = f'{l1}"{new_n}"' + l2[j+1:]
        else:
            new_l = l
        new_lines.append(new_l)
    new_s = "".join(new_lines)
    with open(new_eaf_fp, "w") as f:
        f.write(new_s)


def dir_path(path_str:str):
    path = Path(path_str).resolve()  # enforce absolute path
    if path.is_dir():
        return path
    raise argparse.ArgumentTypeError(f"{path} not valid, should be a directory")


if __name__ == "__main__":
    # TODO for user interface:
    # - DONE expect directory structure in which all texts have their own dir
    # - and each text dir has one video, one audio, and optionally one .eaf transcript
    # - then the script will create a new video (with offset audio from the audio file)
    # - and if the .eaf is present, it will create an offset .eaf and an offset .srt
    # - pass single text directory path as arg

    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path", type=dir_path)
    args = parser.parse_args()

    text_name = args.dir_path.stem

    text_dir = Path("/home/kuhron/langdoc-script-collection/example_files") / text_name
    if not text_dir.is_absolute():
        warn("text dir is not absolute path")
    audio_ext = ".WAV"
    video_ext = ".MTS"

    # Note: ASER was recorded on Zoom H5 with no lapel mic in 2021, MAMBU was recorded on Zoom H6 with lapel mic in 2023

    tmp_dir_path = get_tmp_dir_path(args.dir_path)
    create_tmp_dir(tmp_dir_path)

    audio_fps = list(text_dir.glob("*"+audio_ext))
    if len(audio_fps) != 1:
        raise Exception(f"there should be exactly one audio file ({audio_ext}) in the directory")
    video_fps = list(text_dir.glob("*"+video_ext))
    if len(video_fps) != 1:
        raise Exception(f"there should be exactly one video file ({video_ext}) in the directory")

    audio_fp ,= audio_fps
    video_fp ,= video_fps

    if not audio_fp.is_absolute():
        warn("audio fp is not absolute")
    if not video_fp.is_absolute():
        warn("video fp is not absolute")

    # TODO if audio is stereo, make mono tmp file (for computing correlations)
    # TODO if audio is stereo, use the stereo not mono file for new video

    audio_from_video_fp = av.get_tmp_fp_for_audio_from_video(video_fp)
    av.write_audio_from_video_to_new_audio_file(video_fp, audio_from_video_fp)

    if wv.audio_fp_is_stereo(audio_fp):
        assert audio_fp.parent == text_dir, audio_fp.parent
        audio_mono_output_fp = wv.get_tmp_fp_for_mono_audio(audio_fp, maintain_parent=False)
        assert audio_mono_output_fp.parent == tmp_dir_path, audio_mono_output_fp.parent
        wv.stereo_wav_to_mono(audio_fp, audio_mono_output_fp)
        audio_fp_to_correlate = audio_mono_output_fp
    else:
        audio_fp_to_correlate = audio_fp
    
    if wv.audio_fp_is_stereo(audio_from_video_fp):
        assert audio_from_video_fp.parent == tmp_dir_path, audio_from_video_fp.parent
        video_audio_mono_output_fp = wv.get_tmp_fp_for_mono_audio(audio_from_video_fp, maintain_parent=True)
        assert video_audio_mono_output_fp.parent == tmp_dir_path, video_audio_mono_output_fp.parent
        wv.stereo_wav_to_mono(audio_from_video_fp, video_audio_mono_output_fp)
        video_audio_fp_to_correlate = video_audio_mono_output_fp
    else:
        video_audio_fp_to_correlate = audio_from_video_fp

    print(f"will correlate these two audio files:\n{audio_fp_to_correlate}\n{video_audio_fp_to_correlate}")

    input("check")
    # once done with everything, give user option to delete the tmp files or keep them to run script again faster next time
    delete_tmp_dir(tmp_dir_path)
    

    # UNSORTED

    # video_audio_mono_fp, *audio_fps = create_mono_wavs_from_video_file(text_dir, video_fname, audio_prefix, tracks)
    # audio_fnames = [os.path.basename(audio_fp) for audio_fp in audio_fps]
    # print(f"{audio_fnames = }")

    if all(os.path.exists(get_correlation_fp(audio_fname, text_dir)) for audio_fname in audio_fnames):
        print(f"all correlations already computed")
    else:
        rms_window_seconds = 0.2
        rms_window_samples = int(round(rms_window_seconds * RATE))

        v_arr = get_array_from_file(video_audio_mono_fp)
        v_arr_rms = sliding_rms(v_arr, rms_window_samples)
        v_len = len(v_arr_rms)

        for audio_fname in audio_fnames:
            make_correlation_file(video_dir=text_dir, v_arr_rms=v_arr_rms, audio_fname=audio_fname, rms_window_samples=rms_window_samples)

    best_offset_samples = get_max_correlation_position(audio_fnames, text_dir)
    print(f"{best_offset_samples = }")

    audio_path = Path(text_dir) / audio_fnames[0]
    subtitles_path = Path("/home/kuhron/Horokoi/Transcriptions") / "Sessions2023/MAMBU/SubtitlesHk_Raw.srt"

    extension_to_write = ".MTS"
    # extension_to_write = ".mp4"
    new_video_path = Path("test").with_suffix(extension_to_write)
    if new_video_path.exists():
        raise FileExistsError(new_video_path)

    offset_s = 0 # best_offset_samples / RATE
    new_video = replace_audio_in_video_clip(video_path, audio_path, offset_s)
    # new_video = add_subtitle_to_video_clip(new_video, subtitles_path, offset_s)
    write_video_clip_to_file(new_video, new_video_path)

    sys.exit()


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
