import util.Correlation as cor
from util.VideoAudioAligningOrganization import get_tmp_dir_path

import os

from pathlib import Path

def create_shifted_eaf_file_helper(existing_eaf_fp, new_eaf_fp, best_offset_samples, allow_overwrite=False):
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
    print(f"created new .eaf transcript file with new timestamps: {new_eaf_fp}")

def create_shifted_eaf_file_from_text_dir(text_dir: Path):
    tmp_dir = get_tmp_dir_path(text_dir)
    corr_fp = cor.get_correlation_fp(tmp_dir)
    best_offset_samples = cor.get_max_correlation_position(corr_fp)
    create_shifted_eaf_file_helper(text_dir / "MAMBU.eaf", text_dir / "MAMBU_aligned.eaf", best_offset_samples)

if __name__ == "__main__":
    create_shifted_eaf_file_from_text_dir()