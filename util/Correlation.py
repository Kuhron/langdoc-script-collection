import numpy as np
from pathlib import Path
from warnings import warn

import util.WavFiles as wv
from util.SoundFileStatistics import sliding_rms, samples_to_seconds, seconds_to_samples, DEFAULT_RMS_WINDOW_SECONDS
from util.VideoAudioAligningOrganization import get_single_audio_and_video_fps_from_text_dir, get_tmp_dir_path
from util.FileTypeDetection import DEFAULT_AUDIO_EXTENSION, DEFAULT_VIDEO_EXTENSION
import util.AudioOfVideoFiles as av


def get_correlation_from_offset(v_arr_rms, a_arr_rms, offset_samples):
    # start audio earlier with negative offset, later with positive offset
    # so since our zero point is both files starting at the same time and potentially ending at different times, when have negative offset we should chop off the front of the audio, and when we have positive offset we should pad the front of the audio
    assert type(offset_samples) is int
    if offset_samples < 0:
        new_a_arr_rms = a_arr_rms[-offset_samples:]
    else:
        new_a_arr_rms = np.concatenate([np.zeros((offset_samples,)), a_arr_rms])
    v_len = len(v_arr_rms)
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


def get_rms_array_from_audio_file(audio_fp, rms_window_samples=None):
    if rms_window_samples is None:
        rms_window_samples = seconds_to_samples(DEFAULT_RMS_WINDOW_SECONDS)
    a_arr = wv.get_array_from_file(audio_fp)
    a_arr_rms = sliding_rms(a_arr, rms_window_samples)
    return a_arr_rms


def create_audio_files_to_correlate(text_dir: Path):
    audio_fp, video_fp = get_single_audio_and_video_fps_from_text_dir(text_dir, audio_ext=DEFAULT_AUDIO_EXTENSION, video_ext=DEFAULT_VIDEO_EXTENSION)

    # if audio is stereo, make mono tmp file (for computing correlations)
    # if audio is stereo, use the stereo not mono file for new video

    audio_from_video_fp = av.get_tmp_fp_for_audio_from_video(video_fp)
    av.write_audio_from_video_to_new_audio_file(video_fp, audio_from_video_fp)

    tmp_dir_path = get_tmp_dir_path(text_dir)

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
    return audio_fp_to_correlate, video_audio_fp_to_correlate


def make_correlation_file_from_text_dir(text_dir: Path) -> None:
    tmp_dir = get_tmp_dir_path(text_dir, create_if_absent=True)
    corr_fp = get_correlation_fp(tmp_dir)

    if corr_fp.exists():
        print(f"all correlations already computed")
    else:
        audio_fp_to_correlate, video_audio_fp_to_correlate = create_audio_files_to_correlate(text_dir)
        rms_window_samples = seconds_to_samples(DEFAULT_RMS_WINDOW_SECONDS)
        make_correlation_file_from_audios(video_audio_fp_to_correlate, audio_fp_to_correlate, rms_window_samples, corr_fp)


def make_correlation_file_from_audios(audio_fp_1, audio_fp_2, rms_window_samples, corr_fp):
    # Offset applied to second audio file.
    print(f"making correlation file for \n {audio_fp_1 = } \n {audio_fp_2 = }")

    rms_array_1 = get_rms_array_from_audio_file(audio_fp_1, rms_window_samples)
    rms_array_2 = get_rms_array_from_audio_file(audio_fp_2, rms_window_samples)

    # find correlation between audio files at various offsets
    offsets_seconds_all = np.arange(-10, 10, 0.1)
    offsets_samples_all = [int(round(wv.RATE * x)) for x in offsets_seconds_all]
    correlations = []

    print(f"{rms_array_1.shape = }")
    print(f"{rms_array_2.shape = }")

    print(f"making correlation")
    correlations, offsets_samples_used = find_correlations_brute_force(rms_array_1, rms_array_2, offsets_samples_all)

    assert len(offsets_samples_used) == len(correlations)

    with open(corr_fp, "w") as f:
        for i in range(len(offsets_samples_used)):
            f.write(f"{offsets_samples_used[i]}\t{correlations[i]}\n")
    print(f"wrote correlations to {corr_fp}")


def get_correlation_fp(temp_dir: Path) -> Path:
    corr_fname = "corr.txt"
    corr_fp = temp_dir / corr_fname
    return corr_fp


def get_text_dir_from_correlation_fp(corr_fp: Path) -> Path:
    par = corr_fp.parent
    assert par.name == ".tmp", "correlation fp is not in a .tmp directory"
    return par.parent


def get_max_correlation_position(corr_fp: Path) -> int:
    if not corr_fp.exists():
        # create it
        text_dir = get_text_dir_from_correlation_fp(corr_fp)
        make_correlation_file_from_text_dir(text_dir)

    discrepancy_tolerance = 0.05 * wv.RATE

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
    
    max_corr = max(this_corr_series)
    if max_corr < 0.5:
        warn(f"max correlation is very low ({max_corr:.2f}); are you sure you have the correct video and audio files?")
    best_offset = offsets[this_corr_series.index(max_corr)]  # don't optimize prematurely?

    print(f"{best_offset = }")

    if abs(best_offset - min(offsets)) <= discrepancy_tolerance or abs(best_offset - max(offsets)) <= discrepancy_tolerance:
            raise Exception(f"Warning: best offset is too close to min or max offset; you probably need to expand the window of offsets checked; {best_offset = }")

    return best_offset