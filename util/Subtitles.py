import os
import sys
from pathlib import Path

from util.Eaf import get_texts_and_times_from_eaf, get_existing_eaf_fp_from_text_dir



def read_interleaved_text(text_fp: Path):
    text_lines = []
    block_dict = {}
    current_line = None
    with open(text_fp, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.endswith("."):
            try:
                n = int(line[:-1])
            except ValueError:
                pass

        if "----" in line:
            text_lines.append(block_dict)
            block_dict = {}
        elif ":" in line:
            split_line = line.split(":")
            line_lang = split_line[0]
            line_text = ":".join(split_line[1:])
            assert line_lang not in block_dict, f"language label {line_lang!r} already present in line {n}"
            block_dict[line_lang] = line_text.strip()

    return text_lines


def create_srt_file_for_languages(text_dir, language_labels):
    if language_labels is None:
        raise ValueError("need to pass --langs argument")
    print(language_labels)
    
    text_lines = read_interleaved_text(text_dir / "InterleavedText.txt")

    srt_lines = []
    for i, d in enumerate(text_lines):
        lang_strs = []
        for lang in language_labels:
            try:
                lang_s = d[lang]
            except KeyError:
                raise Exception(f"language label {lang!r} not found in line {i+1}")
            lang_strs.append(lang_s)
        srt_lines.append("\n".join(lang_strs))
    
    lang_abbrev = "_".join(language_labels)
    output_fp = text_dir / f"Subtitles_{lang_abbrev}.srt"
    eaf_fp = get_existing_eaf_fp_from_text_dir(text_dir, prompt_if_not_aligned=True)
    _, _, start_times, end_times = get_texts_and_times_from_eaf(eaf_fp)
    create_single_language_srt(srt_lines, start_times=start_times, end_times=end_times, out_file=output_fp)



def create_single_language_srt(lines, start_times, end_times, out_file):
    # https://en.wikipedia.org/wiki/SubRip#SubRip_text_file_format
    if os.path.exists(out_file):
        print(f".srt file exists: {out_file}\nAborting.")
        sys.exit()

    line_number_to_write = 1  # may not be the same as just i+1 if we skip some lines
    lines_to_write = []
    for i, line in enumerate(lines):
        start_time_ms = max(0, start_times[i])
        end_time_ms = max(0, end_times[i])
        assert start_time_ms < end_time_ms or start_time_ms == end_time_ms == 0, f"bad start and end times: {start_time_ms}, {end_time_ms}"
        if end_time_ms == 0:
            print(f"offset led to line being excluded ({i=}): {line!r}")
            continue
        start_time_str = get_srt_time_str(start_time_ms)
        end_time_str = get_srt_time_str(end_time_ms)
        line_to_write = f"{line_number_to_write}\n{start_time_str} --> {end_time_str}\n{line}\n\n"
        lines_to_write.append(line_to_write)
        line_number_to_write += 1
    
    with open(out_file, "w") as f:
        for line in lines_to_write:
            f.write(line)
    print(f"wrote subtitles to {out_file}")


def create_dual_language_srt(lines_1, lines_2, lang_abbrev_1, lang_abbrev_2, start_times, end_times, out_file):
    lines = [l1 + "\n" + l2 for l1, l2 in zip(lines_1, lines_2)]
    lang_abbrev = lang_abbrev_1 + lang_abbrev_2
    create_single_language_srt(lines, lang_abbrev, start_times, end_times, out_file)


def get_srt_time_str(time_ms):
    rest_s, ms = divmod(time_ms, 1000)
    rest_m, s = divmod(rest_s, 60)
    h, m = divmod(rest_m, 60)
    return str(h).rjust(2, "0") + ":" + str(m).rjust(2, "0") + ":" + str(s).rjust(2, "0") + "," + str(ms).rjust(3, "0")


def create_sfm_file(targlang_lines, contlang_lines, session_dir):
    with open(os.path.join(session_dir, "SfmOutput.sfm"), "w") as f:
        i = 0
        # f.write("\\_sh\tv3.0\t520\tText\n")
        f.write("\\id Auto-generated text\n")
        for targlang, contlang in zip(targlang_lines, contlang_lines):
            targlang = targlang.strip().replace(" ", "\t")
            contlang = contlang.strip()
            # f.write(f"\\ref wkjauto{i}\n")  # so Flex knows it's a new line, not like 1.1, 1.2, 1.3, etc.
            f.write("\\ref\n")  # so Flex knows it's a new line, not like 1.1, 1.2, 1.3, etc.
            f.write(f"\\tx {targlang}\t\n")
            f.write(f"\\ft {contlang}\t\n")
            f.write("\\pb\n")  # attempting to make my own "ParagraphBreak" tag
            f.write("\n")
            i += 1
    print("done creating sfm file")



def get_subtitles_and_other_lines_from_srt_file(lang_code, session_dir, other_lines_already_seen=None):
    other_lines = [x for x in other_lines_already_seen] if other_lines_already_seen is not None else []
    try:
        with open(os.path.join(session_dir, f"Subtitles{lang_code}.srt")) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"you need to make subtitle file for {lang_code} (but make sure to align time first!)")
        return

    subtitles = []
    for i, line in enumerate(lines):
        # print(i, line)
        if i % 4 == 0:
            try:
                assert int(line.strip()) == i / 4 + 1, f"line {i=}: {line}"
            except ValueError:
                print(f"line {i=}: {line}")
                raise
        elif i % 4 == 1:
            assert "-->" in line
        elif i % 4 == 2:
            # subtitle line, just take whatever's there
            pass
        elif i % 4 == 3:
            assert line == "\n"
        else:
            raise ValueError("impossible")

        subtitles.append(line if i % 4 == 2 else None)
        if len(other_lines) == i:
            other_lines.append(None if i % 4 == 2 else line)
        elif len(other_lines) > i:
            if other_lines[i] != (None if i % 4 == 2 else line):
                print("\n".join(f"{x} | {y}" for x,y in zip(subtitles, other_lines)) + "\n")
                raise Exception(f"line {i} of {lang_code} disagrees with that previously found:\nshould be:\n{None if i % 4 == 2 else line}\nbut got:\n{other_lines[i]}")
        else:
            raise Exception("bad line appending, missed something along the way")

    assert len(subtitles) == len(other_lines), f"{len(subtitles) = }, {len(other_lines) = }"
    return subtitles, other_lines
