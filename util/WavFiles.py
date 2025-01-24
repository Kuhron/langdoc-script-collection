import numpy as np


RATE = 44100
MAX_AMPLITUDE = 32767


def get_array_from_file(fp, zoom):
    print(f"opening {fp}")
    with open(fp, "rb") as f:
        contents = f.read()

    hx = contents.hex()
    padding = 65536 if zoom else 22  # Audacity uses a different value for some reason

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
