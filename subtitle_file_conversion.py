# Copyright (c) 2024 Wesley Kuhron Jones <wesleykuhronjones@gmail.com>
# Licensed under the MIT License, see below


import argparse
import os
import sys

parser = argparse.ArgumentParser(
    prog='TextFormatConverter',
    description='This program converts between text formats found in language documentation: .eaf from Saymore, .flextext from FLEx, and .srt subtitles for YouTube.',
)
parser.add_argument("--tl", dest="target_language", help="target language name, e.g. 'Horokoi'", required=True)
parser.add_argument("--tls", dest="target_language_short", help="target language abbreviation, e.g. 'Hk'", required=True)
parser.add_argument("--cl", dest="contact_language", help="contact language name, e.g. 'Tok Pisin'", required=True)
parser.add_argument("--cls", dest="contact_language_short", help="contact language abbreviotion, e.g. 'Tp'", required=True)
parser.add_argument("-i", "--in-file", help="path of input file", required=True)
parser.add_argument("-o", "--out-file", help="path of output file", required=True)

args = parser.parse_args()
print(args)

allowed_formats = [".eaf", ".flextext", ".srt"]

in_fname, in_ext = os.path.splitext(args.in_file)
out_fname, out_ext = os.path.splitext(args.out_file)
if in_ext not in allowed_formats:
    raise Exception(f"Converting from/to {in_ext} is not supported")
if out_ext not in allowed_formats:
    raise Exception(f"Converting from/to {out_ext} is not supported")
print(f"converting from {in_ext} format to {out_ext} format")

sys.exit()



contact_language_is_english = contlang_name == "English"


# extract the text labels in each language and print them for pasting into Flex

import os
import sys
from xml.etree import ElementTree as ET


def create_srt_file_from_eaf(fp, session_dir, subtitle_offset_to_add, srt_fp=None):
    assert fp.endswith(".eaf"), "fp must end with '.eaf'"

    targlang_texts, contlang_texts, start_times, end_times = get_texts_and_times_from_eaf(eaf_fp)
    targlang_lines = targlang_texts
    contlang_lines = contlang_texts
    create_srt_targlang_and_contlang(targlang_lines, contlang_lines, start_times, end_times, session_dir, subtitle_offset_to_add)
    write_texts_interleaved(targlang_texts, contlang_texts, session_dir)
    targlang_subtitles, other_lines = get_subtitles_and_other_lines(f"{targlang_abbrev}_Raw", session_dir, other_lines_already_seen=None)
    contlang_subtitles, other_lines = get_subtitles_and_other_lines(f"{contlang_abbrev}_Raw", session_dir, other_lines_already_seen=other_lines)

    lang_code = f"{targlang_abbrev}{contlang_abbrev}"
    eng_subtitles = None
    create_srt_interleaved(lang_code, session_dir, targlang_subtitles, contlang_subtitles, eng_subtitles, other_lines, srt_fp=srt_fp)


def create_srt_targlang_and_contlang(targlang_lines, contlang_lines, start_times, end_times, session_dir, subtitle_offset_to_add):
    for lang_code in [targlang_abbrev, contlang_abbrev]:
        # don't bother with one for contlang-english or targlang-contlang-english, we mostly care about people understanding the target language in either the contact language or English
        # so of all 8 possibilities: users can do: 0, targ, cont, eng, targ-cont, targ-eng, (X)cont-engEng, (X)targ-cont-eng

        with open(os.path.join(session_dir, f"Subtitles{lang_code}_Raw.srt"), "w") as f:
            # https://en.wikipedia.org/wiki/SubRip#SubRip_text_file_format
            index_to_write = 1
            for i in range(len(targlang_lines)):
                start_time_ms = max(0, start_times[i] + subtitle_offset_to_add)
                end_time_ms = max(0, end_times[i] + subtitle_offset_to_add)
                assert start_time_ms < end_time_ms or start_time_ms == end_time_ms == 0
                if end_time_ms == 0:
                    # the offset led to this segment being excluded
                    continue
                start_time_str = get_srt_time_str(start_time_ms)
                end_time_str = get_srt_time_str(end_time_ms)
                if lang_code == targlang_abbrev:
                    subtitle_str = targlang_lines[i]
                elif lang_code == contlang_abbrev:
                    subtitle_str = contlang_lines[i]
                else:
                    raise ValueError(f"{lang_code = }")
                f.write(f"{index_to_write}\n{start_time_str} --> {end_time_str}\n{subtitle_str}\n\n")
                index_to_write += 1
        print(f"created srt file for {lang_code}")


def create_srt_interleaved(lang_code, session_dir, targlang_subtitles, contlang_subtitles, eng_subtitles, other_lines, srt_fp=None):
    if srt_fp is None:
        srt_fp = os.path.join(session_dir, f"Subtitles{lang_code}.srt")
    with open(srt_fp, "w") as f:
        for i in range(len(other_lines)):
            lines_this_group = []
            if i % 4 == 2:
                if targlang_abbrev in lang_code:
                    lines_this_group.append(targlang_subtitles[i])
                if contlang_abbrev in lang_code:
                    lines_this_group.append(contlang_subtitles[i])
                if "Eng" in lang_code:
                    lines_this_group.append(eng_subtitles[i])
            else:
                lines_this_group.append(other_lines[i])

            assert not any(x is None for x in lines_this_group), f"got Nones in {lang_code} with {i=}\n{lines_this_group = }"
            line = "".join(lines_this_group)
            f.write(line)
    print(f"wrote interleaved srt file for {lang_code}: {srt_fp}")


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


def get_srt_time_str(time_ms):
    rest_s, ms = divmod(time_ms, 1000)
    rest_m, s = divmod(rest_s, 60)
    h, m = divmod(rest_m, 60)
    return str(h).rjust(2, "0") + ":" + str(m).rjust(2, "0") + ":" + str(s).rjust(2, "0") + "," + str(ms).rjust(3, "0")


def get_texts_and_times_from_eaf(fp):
    assert fp.endswith(".eaf")

    targlang_texts = []
    contlang_texts = []
    start_times = []
    end_times = []

    tree = ET.parse(fp)
    root = tree.getroot()
    # Horokoi is the TIER with LINGUISTIC_TYPE_REF="Transcription"
    # Tok Pisin is the TIER with LINGUISTIC_TYPE_REF="Translation"
    tier_els = root.findall("TIER")
    targlang_tier_el, = [el for el in tier_els if el.attrib["LINGUISTIC_TYPE_REF"] == "Transcription"]
    contlang_tier_el, = [el for el in tier_els if el.attrib["LINGUISTIC_TYPE_REF"] == "Translation"]
    time_order_el, = root.findall("TIME_ORDER")
    time_slot_els = time_order_el.findall("TIME_SLOT")
    time_ms_by_id = {el.attrib["TIME_SLOT_ID"] : int(el.attrib["TIME_VALUE"]) for el in time_slot_els}

    annotation_id_order = []
    targlang_by_annotation_id = {}
    contlang_by_annotation_id = {}
    start_times_by_annotation_id = {}
    end_times_by_annotation_id = {}

    targlang_annotation_els = targlang_tier_el.findall("ANNOTATION")
    for el in targlang_annotation_els:
        align_el, = el.findall("ALIGNABLE_ANNOTATION")
        annotation_id = align_el.attrib["ANNOTATION_ID"]
        annotation_id_order.append(annotation_id)
        start_time_ref = align_el.attrib["TIME_SLOT_REF1"]
        end_time_ref = align_el.attrib["TIME_SLOT_REF2"]
        start_times_by_annotation_id[annotation_id] = time_ms_by_id[start_time_ref]
        end_times_by_annotation_id[annotation_id] = time_ms_by_id[end_time_ref]
        val_el, = align_el.findall("ANNOTATION_VALUE")
        targlang_text = val_el.text
        if targlang_text == "%ignore%":
            targlang_text = "..."
        elif targlang_text is None:
            targlang_text = "..."
        targlang_by_annotation_id[annotation_id] = targlang_text

    # the other tier has a different structure in the XML
    contlang_annotation_els = contlang_tier_el.findall("ANNOTATION")
    for el in contlang_annotation_els:
        ref_el, = el.findall("REF_ANNOTATION")
        annotation_id = ref_el.attrib["ANNOTATION_REF"]
        # THIS annotation, the Tok Pisin one, is ANNOTATION_ID, but we want to match it with the corresponding Horokoi, which is ANNOTATION_REF
        val_el, = ref_el.findall("ANNOTATION_VALUE")
        contlang_text = val_el.text
        if contlang_text is None:
            contlang_text = ""
        # there don't seem to be %ignore% values here
        contlang_by_annotation_id[annotation_id] = contlang_text

    # now stitch the two languages together into their lists
    for annotation_id in annotation_id_order:
        targlang_text = targlang_by_annotation_id[annotation_id]
        try:
            contlang_text = contlang_by_annotation_id[annotation_id]
        except KeyError:
            assert targlang_text == "...", targlang_text
            contlang_text = ""
        targlang_texts.append(targlang_text)
        contlang_texts.append(contlang_text)
        start_times.append(start_times_by_annotation_id[annotation_id])
        end_times.append(end_times_by_annotation_id[annotation_id])

    return targlang_texts, contlang_texts, start_times, end_times


def write_texts_interleaved(targlang_texts, contlang_texts, session_dir):
    assert len(targlang_texts) == len(contlang_texts)
    with open(os.path.join(session_dir, f"{targlang_abbrev}Text.txt"), "w") as f:
        for i, l in enumerate(targlang_texts):
            f.write(f"{i+1}. {l}\n")
    with open(os.path.join(session_dir, f"{contlang_abbrev}Text.txt"), "w") as f:
        for i, l in enumerate(contlang_texts):
            f.write(f"{i+1}. {l}\n")
    with open(os.path.join(session_dir, "InterleavedText.txt"), "w") as f:
        for i in range(len(targlang_texts)):
            targlang_s = targlang_texts[i]
            contlang_s = contlang_texts[i]
            f.write(f"{i+1}.\n{targlang_s}\n{contlang_s}\n----\n")


def get_subtitles_and_other_lines(lang_code, session_dir, other_lines_already_seen=None):
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


def run(fnames):
    form = None
    if all(fname.endswith("TranscriptionLabels.txt") for fname in fnames):
        form = "Audacity"
    elif all(fname.endswith("annotations.eaf") for fname in fnames):
        form = "SayMore"
    else:
        raise Exception("input files must be all Audacity labels or all SayMore annotations")

    fps = [os.path.join(session_dir, fname) for fname in fnames]


    # read the input files and sort out which language is which

    if form == "Audacity":
        lines_by_file_index = {}
        for i, fp in enumerate(fps):
            with open(fp) as f:
                lines_by_file_index[i] = f.readlines()

        labels_by_file_index_and_time = {}
        max_n_values = 0
        for fp_i, lines in lines_by_file_index.items():
            for l in lines:
                lst = l.strip().split("\t")
                t0 = float(lst[0])
                t1 = float(lst[1])
                text = lst[2]
                assert len(lst) == 3, lst
                key = (fp_i, t0, t1)  # ensure earlier files' lines are earlier, don't sort only by time
                if key not in labels_by_file_index_and_time:
                    labels_by_file_index_and_time[key] = []
                labels_by_file_index_and_time[key].append(text)
                max_n_values = max(max_n_values, len(labels_by_file_index_and_time[key]))

        assert max_n_values == 2, "too many languages"

        # have the user tell which language is which
        targlang_index = 0
        contlang_index = 1
        targlang_texts = []
        contlang_texts = []
        start_times = []
        end_times = []

        for k in sorted(labels_by_file_index_and_time.keys()):
            print("TODO: get time from Audacity labels")
            raise NotImplementedError
            texts = labels_by_file_index_and_time[k]
            for i, text in enumerate(texts):
                print(f"{i}: {text}")
            istr = input(f"which index is Horokoi here? (default {targlang_index})")
            if istr == "":
                # don't change the index
                pass
            else:
                targlang_index = int(istr)
                contlang_index = 1 - targlang_index
            targlang_text = texts[targlang_index]
            contlang_text = texts[contlang_index]
            targlang_texts.append(targlang_text)
            contlang_texts.append(contlang_text)
            print()

    elif form == "SayMore":
        targlang_texts = []
        contlang_texts = []
        start_times = []
        end_times = []
        for fp in fps:
            these_targlang_texts, these_contlang_texts, these_start_times, these_end_times = get_texts_and_times_from_eaf(fp)
            targlang_texts += these_targlang_texts
            contlang_texts += these_contlang_texts
            start_times += these_start_times
            end_times += these_end_times
    else:
        raise Exception(f"format of input is {form}")


    # write the outputs once the input has been parsed / sorted
    write_texts_interleaved(targlang_texts, contlang_texts, session_dir)

    targlang_lines = targlang_texts
    contlang_lines = contlang_texts
    assert len(targlang_lines) == len(contlang_lines) == len(start_times) == len(end_times)

    # create_sfm_file(targlang_lines, contlang_lines, session_dir)

    create_srt_targlang_and_contlang(targlang_lines, contlang_lines, start_times, end_times, session_dir, subtitle_offset_to_add)

    # once raw subtitle files are written, I need to make cleaned versions of targlang and contlang, and also an Eng one where I translate contact language to English, then run the program again and it will make the combined ones for targ-cont and targ-eng
    # on YouTube, select subtitle languages that encode which combination users want, and put the key in the description, e.g. Hiri Motu = Horokoi (target language), Tok Pisin = Tok Pisin (contact language), English = English, Tamil = Horokoi + Tok Pisin, Estonian = Horokoi + English
    other_lines = None
    for lang_code in [f"{targlang_abbrev}_Cleaned", f"{contlang_abbrev}_Cleaned", "Eng"]:
        print(f"{lang_code=}")
        subtitles, other_lines = get_subtitles_and_other_lines(lang_code, session_dir, other_lines_already_seen=other_lines)
        if lang_code == f"{targlang_abbrev}_Cleaned":
            targlang_subtitles = [x for x in subtitles]
        elif lang_code == f"{contlang_abbrev}_Cleaned":
            contlang_subtitles = [x for x in subtitles]
        elif lang_code == "Eng":
            eng_subtitles = [x for x in subtitles]
        else:
            raise ValueError(f"{lang_code = }")

    # now interleave subtitles
    for lang_code in [f"{targlang_abbrev}{contlang_abbrev}", f"{targlang_abbrev}Eng"]:
        print(f"{lang_code=}")

        create_srt_interleaved(lang_code, session_dir, targlang_subtitles, contlang_subtitles, eng_subtitles, other_lines)



if __name__ == "__main__":
    # for aligning the subtitles, pick a segment after you upload the first Horokoi subtitle file and watch the YouTube video with it, find in the subtitle editor where you want it to start (desired_start) vs where it starts in the .srt file (srt_start)
    # do this BEFORE doing the cleaning of target language and contact language files or translating to English, so that their times will be as desired on YouTube
    # - alternatively, for those files where you've already run VideoAudioAligning.py, use the EAF with the same filename as the video (video fp with .MTS replaced by .eaf)

    use_offset = False
    if use_offset:
        srt_start_ms = 27694
        desired_start_s = 25
        desired_start_frame = 21

        frames_per_s = 30
        desired_start_ms = int(1000*(desired_start_s + desired_start_frame/frames_per_s))
        subtitle_offset_to_add = desired_start_ms - srt_start_ms
    else:
        subtitle_offset_to_add = 0

    run_in_transcriptions_dir = False
    if run_in_transcriptions_dir:
        session_dir = "Sessions/VD5"
        # session_dirs = [os.path.join("Sessions", x) for x in os.listdir("Sessions") if os.path.isdir(os.path.join("Sessions", x))]
        print(f"{session_dir = }")
        fnames = [x for x in os.listdir(session_dir) if x.endswith(".annotations.eaf") or x.endswith("TranscriptionLabels.txt")]
        run(fnames)

    run_in_ehd_paradisec_files_renamed_dir = True
    if run_in_ehd_paradisec_files_renamed_dir:
        parent_dir = "/media/wesley/LaCie/Horokoi/2023_Backup/FilesRenamed/"
        items = os.listdir(parent_dir)
        # find all pairs of MTS and EAF files that have same filename
        for item in items:
            session_dir = os.path.join(parent_dir, item)
            fnames = [x for x in os.listdir(session_dir) if x.endswith(".MTS") or x.endswith(".eaf")]
            bases = set(os.path.splitext(fname)[0] for fname in fnames)
            matches = [x for x in bases if os.path.exists(os.path.join(session_dir, x + ".MTS")) and os.path.exists(os.path.join(session_dir, x + ".eaf"))]
            if len(matches) > 0:
                for base in matches:
                    eaf_fp = os.path.join(parent_dir, item, base + ".eaf")
                    print(eaf_fp)
                    srt_fp = eaf_fp.replace(".eaf", ".srt")
                    create_srt_file_from_eaf(eaf_fp, session_dir, subtitle_offset_to_add, srt_fp)
