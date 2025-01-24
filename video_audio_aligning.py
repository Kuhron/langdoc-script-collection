# Copyright (c) 2023 Wesley Kuhron Jones <wesleykuhronjones@gmail.com>
# Licensed under the MIT License, see below


### PARAMS TO BE SET BY USER ###

parent_dir = "/home/kuhron/langdoc-script-collection/example_files/MAMBU"
video_fname = "HK1-MAMBU-REC.MTS"
audio_prefix = "HK1-MAMBU-REC"

# Note: ASER was recorded on Zoom H5 with no lapel mic in 2021, MAMBU was recorded on Zoom H6 with lapel mic in 2023


### END USER PARAMS ###


import os
import numpy as np
import matplotlib.pyplot as plt
import moviepy
from pydub import AudioSegment
import sys

from util.SoundFileStatistics import sliding_rms
from util.WavFiles import RATE, MAX_AMPLITUDE, get_array_from_file


def stereo_wav_to_mono(fp):
    if fp.endswith(".wav"):
        mono_fp = fp.replace(".wav", "-Mono.wav")
    elif fp.endswith(".WAV"):
        mono_fp = fp.replace(".WAV", "-Mono.WAV")
    else:
        raise Exception(f"bad filename: {fp}")
    if os.path.exists(mono_fp):
        print(f"file exists, skipping; {mono_fp}")
    else:
        sound = AudioSegment.from_wav(fp)
        sound = sound.set_channels(1)
        sound.export(mono_fp, format="wav")
    return mono_fp


def create_mono_wavs_from_video_file(video_dir, video_fname, audio_prefix, tracks):
    video_fp = os.path.join(video_dir, video_fname)
    video_audio_fp = os.path.join(video_dir, "AudioFromVideo.wav")  # TODO put original filename in this filename somewhere
    if os.path.exists(video_audio_fp):
        print(f"file exists, skipping; {video_audio_fp}")
    else:
        video = moviepy.VideoFileClip(video_fp)
        video.audio.write_audiofile(video_audio_fp)
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
    offsets_samples_used = []
    correlations = []
    for offset_samples in offsets_samples:
        corr = get_correlation_from_offset(v_arr_rms, a_arr_rms, offset_samples)
        print(f"{offset_samples = }, {corr = :+.6f}\t\t\r")
        offsets_samples_used.append(offset_samples)  # redundant but whatever
        correlations.append(corr)
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
    offsets_samples_all = [int(round(RATE * x)) for x in offsets_seconds_all]
    correlations = []
    a_arr = get_array_from_file(audio_fp)
    a_arr_rms = sliding_rms(a_arr, rms_window_samples)

    print(f"{v_arr_rms.shape}")
    print(f"{a_arr_rms.shape}")
    input("check")

    # make it so we slide the audio and keep the video in place, since I am making edited .eaf files that will match the video time
    print(f"making correlation")
    correlations, offsets_samples_used = find_correlations_brute_force(v_arr_rms, a_arr_rms, offsets_samples_all)
    # correlations, offsets_samples_used = find_correlations_binary_search(v_arr_rms, a_arr_rms, offsets_samples_all)

    offsets_seconds_used = [x/RATE for x in offsets_samples_used]
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
    discrepancy_tolerance = 0.05 * RATE
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

    # debug
    for corr, corr_fp in zip(corr_series, corr_fps):
        plt.plot(corr, label=corr_fp)
    plt.show()

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



if __name__ == "__main__":
    video_dir = parent_dir

    audio_fps_in_dir_raw = [x for x in os.listdir(video_dir) if x.startswith(audio_prefix) and x.endswith(".WAV")]
    tracks = [x.replace(audio_prefix+"_", "").replace(".WAV", "") for x in audio_fps_in_dir_raw]

    # extra audio file if we've already run the mono wav creation function, don't double it up in the list 
    # (since create_mono_wavs will think it's another audio track like TR1/TR2 
    # and add it to the list of audio files after already adding it by converting the plain LR fname into LR-Mono, 
    # so we'll end up with two LR-Mono in the list)
    tracks = [x for x in tracks if x != "LR-Mono"]

    video_audio_mono_fp, *audio_fps = create_mono_wavs_from_video_file(video_dir, video_fname, audio_prefix, tracks)
    audio_fnames = [os.path.basename(audio_fp) for audio_fp in audio_fps]
    print(f"{audio_fnames = }")

    if all(os.path.exists(get_correlation_fp(audio_fname, video_dir)) for audio_fname in audio_fnames):
        print(f"all correlations already computed")
    else:
        rms_window_seconds = 0.2
        rms_window_samples = int(round(rms_window_seconds * RATE))

        v_arr = get_array_from_file(video_audio_mono_fp)
        v_arr_rms = sliding_rms(v_arr, rms_window_samples)
        v_len = len(v_arr_rms)

        for audio_fname in audio_fnames:
            make_correlation_file(video_dir=video_dir, v_arr_rms=v_arr_rms, audio_fname=audio_fname, rms_window_samples=rms_window_samples)

    best_offset_samples = get_max_correlation_position(audio_fnames, video_dir)
    print(f"{best_offset_samples = }")

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
