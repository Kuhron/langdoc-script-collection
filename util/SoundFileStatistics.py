import numpy as np


def rms(arr):
    return (np.mean(arr**2))**0.5


def sliding_rms(arr, window):
    b = np.zeros(len(arr))
    # pad it with zeros for the missing frames, need window-1 of them
    n_in_front = (window - 1) // 2
    n_in_back = (window - 1) - n_in_front

    a2 = arr**2
    for i in range(len(arr) - window + 1):
        if i % 1000000 == 0:
            print(f"getting sliding rms: {i // 1000000} / {(len(arr) - window + 1) / 1000000:.1f} M")
        if i == 0:
            window_sum = sum(a2[:window])
        else:
            window_sum -= a2[i - 1]
            window_sum += a2[i + window - 1]
        window_mean = window_sum / window
        window_rms = window_mean ** 0.5
        b[i + n_in_front] = window_rms
    return np.array(b)
