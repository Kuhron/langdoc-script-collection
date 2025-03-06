from pathlib import Path

import util.WavFiles as wv
import numpy as np

from util.SoundFileStatistics import sliding_rms


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


def get_rms_array_from_audio_file(audio_fp, rms_window_samples):
    a_arr = wv.get_array_from_file(audio_fp)
    a_arr_rms = sliding_rms(a_arr, rms_window_samples)
    return a_arr_rms


def make_correlation_file(audio_fp_1, audio_fp_2, rms_window_samples, corr_fp):
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


def get_correlation_fp(temp_dir):
    corr_fname = "corr.txt"
    corr_fp = temp_dir / corr_fname
    return corr_fp


def get_max_correlation_position(corr_fp):
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
    
    best_offset = offsets[this_corr_series.index(max(this_corr_series))]  # don't optimize prematurely?

    print(f"{best_offset = }")

    if abs(best_offset - min(offsets)) <= discrepancy_tolerance or abs(best_offset - max(offsets)) <= discrepancy_tolerance:
            raise Exception(f"Warning: best offset is too close to min or max offset; you probably need to expand the window of offsets checked; {best_offset = }")

    return best_offset