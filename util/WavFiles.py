import numpy as np
import wavio


RATE = 44100
MAX_AMPLITUDE = 32767


def get_array_from_file(fp):
    # TODO why is running sliding_rms on this array so much slower than on the one from get_array_from_file_reading_binary_directly?
    arr = wavio.read(fp).data
    m, one = arr.shape
    assert one == 1
    return arr.reshape((m,))


def get_array_from_file_reading_binary_directly(fp, zoom_or_audacity="zoom"):
    if zoom_or_audacity not in ["zoom", "audacity"]:
        raise ValueError(f"Invalid recorder specified: {zoom_or_audacity = !r}, but needs to be either 'zoom' (for Zoom H5 or H6 recorder) or 'audacity' (for Audacity program)")

    print(f"opening {fp}")
    with open(fp, "rb") as f:
        contents = f.read()

    hx = contents.hex()

    # TODO/FIXME there might be bug here due to hardcoding the number of bytes used for padding by different recording devices
    # ideally use a library to get wav data
    padding = 65536 if zoom_or_audacity else 22  # Audacity uses a different value for some reason

    samples = len(hx) / 4 - padding
    assert samples % 1 == 0, f"samples should be an integer, got {samples}"
    samples = int(samples)

    header_hex = hx[:4*padding]

    b = bytes.fromhex(hx[4*padding:])
    assert len(b) == 2 * samples, f"{len(b)} != {2 * samples}"

    # for testing
    # good_sample_range = 1014990, 1015039  # Audacity counts from 0

    arr = []
    # for i in range(*good_sample_range):
    for i in range(samples):
        if i % 1000000 == 0:
            print(f"getting array from WAV file: {i // 1000000} / {samples / 1000000:.1f} M")
        x, y = b[2*i : 2*i+2]
        n = (2**8) * y + x
        if n >= 2**15:
            # the first bit of y is 1
            n = -1 * (2**16 - 1 - n)
        arr.append(n)

    return np.array(arr) / MAX_AMPLITUDE, header_hex
