# Copyright (c) 2023 Wesley Kuhron Jones <wesleykuhronjones@gmail.com>
# Licensed under the MIT License, see below


### PARAMS TO BE SET BY USER ###

# set `zoom` to True if the file was created directly by the Zoom H6, False for Audacity
zoom = True

# selecting the file
n = "0394"
suffix = "Tr1"
fp = f"Transcriptions/temp/ZOOM{n}/ZOOM{n}_{suffix}.WAV"

# what amplitude is considered "quiet", i.e., not containing speech
cutting_amplitude = 0.002

# make a plot of the waveform, RMS, cutting points, etc. for debugging or understanding what the script is doing
plot = False

# width of the sliding window for calculating RMS amplitude
window_seconds = 1/5

# amplitude to amplify the audio segments to
target_amplitude = 0.25

### END USER PARAMS ###


import math
import numpy as np
import matplotlib.pyplot as plt

from util.SoundFileStatistics import sliding_rms
from util.WavFiles import RATE, MAX_AMPLITUDE, get_array_from_file_reading_binary_directly


def get_binary_string(n, big_endian=True):
    assert type(n) is int, type(n)
    assert 0 <= n <= 255
    if n == 0:
        return "0" * 8
    p0 = math.floor(math.log2(n))
    y = n / (2 ** p0)
    s = ""
    while n > 0:
        x, y = divmod(y, 2)
        s += str(int(x))
        if y == 0:
            break
        y *= 2
    assert s[0] == "0"
    s = s[1:]
    l = 1 + p0
    s = s.ljust(l, "0")
    s = s.rjust(8, "0")

    if not big_endian:
        s = s[::-1]
    # print(f"{n} -> {s}")
    return s


def twos_complement(b):
    s = ""
    for c in b:
        if c == "0":
            s += "1"
        elif c == "1":
            s += "0"
        else:
            raise ValueError(c)
    return s


def binary_to_int(b):
    n = 0
    for i in range(len(b)):
        x = int(b[-(i+1)])
        n += x * (2 ** i)
    return n


def get_bytes_from_int(n):
    # clip to max amplitude
    if n < 0:
        n = max(-MAX_AMPLITUDE, n)
        y, x = divmod(n + 2**16 - 1, 2**8)
    else:
        n = min(MAX_AMPLITUDE, n)
        y, x = divmod(n, 2**8)
    if x < 0 or x > 255 or y < 0 or y > 255:
        print(n, x, y)
        raise
    return x, y  # little-endian


def get_cuttable_intervals_from_cut_arr(cut_arr):
    interval_borders = [-0.5]
    for i in range(len(cut_arr) - 1):
        if i % 1000000 == 0:
            print(f"getting interval borders: {i // 1000000} / {len(cut_arr) / 1000000:.1f} M")
        a = cut_arr[i]
        b = cut_arr[i+1]
        if a != b:
            interval_borders.append(i+0.5)
    interval_borders.append(len(cut_arr) - 1 + 0.5)

    cuttable_intervals = []
    non_cuttable_intervals = []
    # in_interval = None
    # start_index = None
    # last_index = None
    for j_i in range(len(interval_borders) - 1):
        j = interval_borders[j_i]
        k = interval_borders[j_i + 1]
        assert j % 1 == 0.5
        assert k % 1 == 0.5
        bounds = (int(j+1), int(k))
        value = cut_arr[int(j+1)]
        if value == 1:
            cuttable_intervals.append(bounds)
        elif value == 0:
            non_cuttable_intervals.append(bounds)
        else:
            raise ValueError(value)
        # the new interval starts at i = j+0.5

    # for i in ?:
        # if x == 1 and (in_interval is None or not in_interval):
        #     # found a new interval, log its start index
        #     interval = (start_index, last_index)
        #     if start_index is not None:
        #         non_cuttable_intervals.append(interval)
        #     start_index = i
        # if x == 0 and (in_interval is None or in_interval):
        #     # left an interval, log the last index as the end
        #     interval = (start_index, last_index)
        #     if start_index is not None:
        #         cuttable_intervals.append(interval)
        #     start_index = i
        # in_interval = x == 1
        # last_index = i
    # if we finish and we're still in an interval, log it
    # if in_interval:
    #     interval = (start_index, last_index)
    #     cuttable_intervals.append(interval)
    return cuttable_intervals, non_cuttable_intervals


def get_cutting_points(rms_arr, cutting_amplitude):
    cut_arr = rms_arr < cutting_amplitude
    cuttable_intervals, sound_intervals = get_cuttable_intervals_from_cut_arr(cut_arr)

    # also want average amplitude within each non-quiet interval
    average_amplitudes = [np.mean(rms_arr[a : b+1]) for a, b in sound_intervals]

    # start - 0.5 and end + 0.5 should always be cutting points, even if they're inside an interval
    start_cut = -0.5
    end_cut = len(rms_arr) - 1 + 0.5
    # if we have cuttable intervals that overlap the start or end, ignore them
    if cuttable_intervals[0][0] == 0:
        cuttable_intervals.remove(cuttable_intervals[0])
    if cuttable_intervals[-1][-1] == len(rms_arr) - 1:
        cuttable_intervals.remove(cuttable_intervals[-1])
    # for all the other ones, put the middle plus 0.5
    cutting_points = [0.5 + int((a + b)/2) for a, b in cuttable_intervals]
    cutting_points = [start_cut] + cutting_points + [end_cut]

    return cutting_points, sound_intervals, average_amplitudes



if __name__ == "__main__":
    window_samples = int(RATE * window_seconds)
    arr, header_hex = get_array_from_file_reading_binary_directly(fp, zoom)
    print("getting sliding rms")
    rms_arr = sliding_rms(arr, window_samples)
    assert len(arr) == len(rms_arr)
    print("done getting sliding rms")

    print("getting cutting points")
    cutting_points, sound_intervals, average_amplitudes = get_cutting_points(rms_arr, cutting_amplitude)
    sound_interval_lengths = [(b - a + 1) / RATE for a, b in sound_intervals]
    asil = sum(sound_interval_lengths) / len(sound_interval_lengths)
    print(f"average sound interval length: {asil:.4f} seconds")
    if not plot:
        del rms_arr
    print("done getting cutting points")

    # put the average in each interval at some value
    print("making new_arr")
    new_arr = arr
    for i in range(len(sound_intervals)):
        cut_a, cut_b = cutting_points[i:i+2]
        amp = average_amplitudes[i]
        r = target_amplitude / amp
        new_arr[int(cut_a + 1) : int(cut_b + 1)] *= r
    new_arr_int = (new_arr * 2**15).astype(int)
    if not plot:
        del new_arr
        del arr
    print("done making new_arr")

    if plot:
        print("making plots")
        plt.subplot(3,1,1)
        plt.plot(arr)

        plt.subplot(3,1,2)
        plt.plot(rms_arr)
        for x in cutting_points:
            plt.plot([x, x], [0, max(rms_arr)], c="r")
        for i in range(len(sound_intervals)):
            a, b = sound_intervals[i]
            y = average_amplitudes[i]
            plt.plot([a, b], [y, y], c="k")

        plt.subplot(3,1,3)
        plt.plot(new_arr)
        for y in [1, -1]:
            plt.plot([0, len(rms_arr) - 1], [y, y], c="k")

        plt.gcf().set_size_inches((12, 6))
        plt.savefig("a.png")

        del arr
        del new_arr
        del rms_arr

    print("making bytes")
    b = np.zeros(2 * len(new_arr_int), dtype=int)
    for i, n in enumerate(new_arr_int):
        if i % 1000000 == 0:
            print(f"making bytes: {i // 1000000} / {len(new_arr_int) / 1000000:.1f} M")
        x, y = get_bytes_from_int(n)
        b[2*i] = x
        b[2*i + 1] = y
        # print(n, x, y, b[max(0, 2*i - 4) : min(2*len(new_arr_int), 2*i + 5)])
    # b = []
    # for n in new_arr_int:
    #     b += list(get_bytes_from_int(n))
    # b = np.array(

    assert b.min() >= 0 and b.max() <= 255
    b = bytes.fromhex(header_hex) + bytes(x for x in b)  # don't cast np array to bytes, it messes the result up somehow
    print("done making bytes")
    output_fp = fp.replace(".", "_Amplified.")
    print(f"writing to {output_fp}")
    with open(output_fp, "wb") as f:
        f.write(b)


# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
