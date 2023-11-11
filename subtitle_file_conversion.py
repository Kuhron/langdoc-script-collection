# extract the text labels in each language and print them for pasting into Flex

import os
import sys
from xml.etree import ElementTree as ET



def create_srt_file_from_eaf(fp, session_dir, subtitle_offset_to_add, srt_fp=None):
    assert fp.endswith(".eaf")

    horokoi_texts, tp_texts, start_times, end_times = get_texts_and_times_from_eaf(eaf_fp)
    hk_lines = horokoi_texts
    tp_lines = tp_texts
    create_srt_hk_and_tp(hk_lines, tp_lines, start_times, end_times, session_dir, subtitle_offset_to_add)
    write_texts_interleaved(horokoi_texts, tp_texts, session_dir)
    hk_subtitles, other_lines = get_subtitles_and_other_lines("Hk_Raw", session_dir, other_lines_already_seen=None)
    tp_subtitles, other_lines = get_subtitles_and_other_lines("Tp_Raw", session_dir, other_lines_already_seen=other_lines)

    lang_code = "HkTp"
    eng_subtitles = None
    create_srt_interleaved(lang_code, session_dir, hk_subtitles, tp_subtitles, eng_subtitles, other_lines, srt_fp=srt_fp)


def create_srt_hk_and_tp(hk_lines, tp_lines, start_times, end_times, session_dir, subtitle_offset_to_add):
    for lang_code in ["Hk", "Tp"]:
        # don't bother with one for TpEng or HkTpEng, we mostly care about people understanding the Horokoi in either one of the contact lgs
        # so of all 8 possibilities: users can do: 0, Hk, Tp, Eng, HkTp, HkEng, (X)TpEng, (X)HkTpEng

        with open(os.path.join(session_dir, f"Subtitles{lang_code}_Raw.srt"), "w") as f:
            # https://en.wikipedia.org/wiki/SubRip#SubRip_text_file_format
            index_to_write = 1
            for i in range(len(hk_lines)):
                start_time_ms = max(0, start_times[i] + subtitle_offset_to_add)
                end_time_ms = max(0, end_times[i] + subtitle_offset_to_add)
                assert start_time_ms < end_time_ms or start_time_ms == end_time_ms == 0
                if end_time_ms == 0:
                    # the offset led to this segment being excluded
                    continue
                start_time_str = get_srt_time_str(start_time_ms)
                end_time_str = get_srt_time_str(end_time_ms)
                if lang_code == "Hk":
                    subtitle_str = hk_lines[i]
                elif lang_code == "Tp":
                    subtitle_str = tp_lines[i]
                else:
                    raise ValueError(f"{lang_code = }")
                f.write(f"{index_to_write}\n{start_time_str} --> {end_time_str}\n{subtitle_str}\n\n")
                index_to_write += 1
        print(f"created srt file for {lang_code}")


def create_srt_interleaved(lang_code, session_dir, hk_subtitles, tp_subtitles, eng_subtitles, other_lines, srt_fp=None):
    if srt_fp is None:
        srt_fp = os.path.join(session_dir, f"Subtitles{lang_code}.srt")
    with open(srt_fp, "w") as f:
        for i in range(len(other_lines)):
            lines_this_group = []
            if i % 4 == 2:
                if "Hk" in lang_code:
                    lines_this_group.append(hk_subtitles[i])
                if "Tp" in lang_code:
                    lines_this_group.append(tp_subtitles[i])
                if "Eng" in lang_code:
                    lines_this_group.append(eng_subtitles[i])
            else:
                lines_this_group.append(other_lines[i])

            assert not any(x is None for x in lines_this_group), f"got Nones in {lang_code} with {i=}\n{lines_this_group = }"
            line = "".join(lines_this_group)
            f.write(line)
    print(f"wrote interleaved srt file for {lang_code}: {srt_fp}")


def create_sfm_file(hk_lines, tp_lines, session_dir):
    with open(os.path.join(session_dir, "SfmOutput.sfm"), "w") as f:
        i = 0
        # f.write("\\_sh\tv3.0\t520\tText\n")
        f.write("\\id Auto-generated text\n")
        for hk, tp in zip(hk_lines, tp_lines):
            hk = hk.strip().replace(" ", "\t")
            tp = tp.strip()
            # f.write(f"\\ref wkjauto{i}\n")  # so Flex knows it's a new line, not like 1.1, 1.2, 1.3, etc.
            f.write("\\ref\n")  # so Flex knows it's a new line, not like 1.1, 1.2, 1.3, etc.
            f.write(f"\\tx {hk}\t\n")
            f.write(f"\\ft {tp}\t\n")
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

    horokoi_texts = []
    tp_texts = []
    start_times = []
    end_times = []

    tree = ET.parse(fp)
    root = tree.getroot()
    # Horokoi is the TIER with LINGUISTIC_TYPE_REF="Transcription"
    # Tok Pisin is the TIER with LINGUISTIC_TYPE_REF="Translation"
    tier_els = root.findall("TIER")
    hk_tier_el, = [el for el in tier_els if el.attrib["LINGUISTIC_TYPE_REF"] == "Transcription"]
    tp_tier_el, = [el for el in tier_els if el.attrib["LINGUISTIC_TYPE_REF"] == "Translation"]
    time_order_el, = root.findall("TIME_ORDER")
    time_slot_els = time_order_el.findall("TIME_SLOT")
    time_ms_by_id = {el.attrib["TIME_SLOT_ID"] : int(el.attrib["TIME_VALUE"]) for el in time_slot_els}

    annotation_id_order = []
    hk_by_annotation_id = {}
    tp_by_annotation_id = {}
    start_times_by_annotation_id = {}
    end_times_by_annotation_id = {}

    hk_annotation_els = hk_tier_el.findall("ANNOTATION")
    for el in hk_annotation_els:
        align_el, = el.findall("ALIGNABLE_ANNOTATION")
        annotation_id = align_el.attrib["ANNOTATION_ID"]
        annotation_id_order.append(annotation_id)
        start_time_ref = align_el.attrib["TIME_SLOT_REF1"]
        end_time_ref = align_el.attrib["TIME_SLOT_REF2"]
        start_times_by_annotation_id[annotation_id] = time_ms_by_id[start_time_ref]
        end_times_by_annotation_id[annotation_id] = time_ms_by_id[end_time_ref]
        val_el, = align_el.findall("ANNOTATION_VALUE")
        hk_text = val_el.text
        if hk_text == "%ignore%":
            hk_text = "..."
        elif hk_text is None:
            hk_text = "..."
        hk_by_annotation_id[annotation_id] = hk_text

    # the other tier has a different structure in the XML
    tp_annotation_els = tp_tier_el.findall("ANNOTATION")
    for el in tp_annotation_els:
        ref_el, = el.findall("REF_ANNOTATION")
        annotation_id = ref_el.attrib["ANNOTATION_REF"]
        # THIS annotation, the Tok Pisin one, is ANNOTATION_ID, but we want to match it with the corresponding Horokoi, which is ANNOTATION_REF
        val_el, = ref_el.findall("ANNOTATION_VALUE")
        tp_text = val_el.text
        if tp_text is None:
            tp_text = ""
        # there don't seem to be %ignore% values here
        tp_by_annotation_id[annotation_id] = tp_text

    # now stitch the two languages together into their lists
    for annotation_id in annotation_id_order:
        hk_text = hk_by_annotation_id[annotation_id]
        try:
            tp_text = tp_by_annotation_id[annotation_id]
        except KeyError:
            assert hk_text == "...", hk_text
            tp_text = ""
        horokoi_texts.append(hk_text)
        tp_texts.append(tp_text)
        start_times.append(start_times_by_annotation_id[annotation_id])
        end_times.append(end_times_by_annotation_id[annotation_id])

    return horokoi_texts, tp_texts, start_times, end_times


def write_texts_interleaved(horokoi_texts, tp_texts, session_dir):
    assert len(horokoi_texts) == len(tp_texts)
    with open(os.path.join(session_dir, "HorokoiText.txt"), "w") as f:
        for i, l in enumerate(horokoi_texts):
            f.write(f"{i+1}. {l}\n")
    with open(os.path.join(session_dir, "TpText.txt"), "w") as f:
        for i, l in enumerate(tp_texts):
            f.write(f"{i+1}. {l}\n")
    with open(os.path.join(session_dir, "InterleavedText.txt"), "w") as f:
        for i in range(len(horokoi_texts)):
            hk_s = horokoi_texts[i]
            tp_s = tp_texts[i]
            f.write(f"{i+1}.\n{hk_s}\n{tp_s}\n----\n")


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
        horokoi_index = 0
        tp_index = 1
        horokoi_texts = []
        tp_texts = []
        start_times = []
        end_times = []

        for k in sorted(labels_by_file_index_and_time.keys()):
            print("TODO: get time from Audacity labels")
            raise NotImplementedError
            texts = labels_by_file_index_and_time[k]
            for i, text in enumerate(texts):
                print(f"{i}: {text}")
            istr = input(f"which index is Horokoi here? (default {horokoi_index})")
            if istr == "":
                # don't change the index
                pass
            else:
                horokoi_index = int(istr)
                tp_index = 1 - horokoi_index
            horokoi_text = texts[horokoi_index]
            tp_text = texts[tp_index]
            horokoi_texts.append(horokoi_text)
            tp_texts.append(tp_text)
            print()

    elif form == "SayMore":
        horokoi_texts = []
        tp_texts = []
        start_times = []
        end_times = []
        for fp in fps:
            these_horokoi_texts, these_tp_texts, these_start_times, these_end_times = get_texts_and_times_from_eaf(fp)
            horokoi_texts += these_horokoi_texts
            tp_texts += these_tp_texts
            start_times += these_start_times
            end_times += these_end_times
    else:
        raise Exception(f"format of input is {form}")


    # write the outputs once the input has been parsed / sorted
    write_texts_interleaved(horokoi_texts, tp_texts, session_dir)

    hk_lines = horokoi_texts
    tp_lines = tp_texts
    assert len(hk_lines) == len(tp_lines) == len(start_times) == len(end_times)

    # create_sfm_file(hk_lines, tp_lines, session_dir)

    create_srt_hk_and_tp(hk_lines, tp_lines, start_times, end_times, session_dir, subtitle_offset_to_add)

    # once raw subtitle files are written, I need to make cleaned versions of Hk and Tp, and also an Eng one where I translate Tok Pisin to English, then run the program again and it will make the combined ones for HkTp and HkEng
    # subtitle languages: Hiri Motu = Horokoi, Tok Pisin = Tok Pisin, English = English, ? = Horokoi + Tok Pisin, ? = Horokoi + English
    other_lines = None
    for lang_code in ["Hk_Cleaned", "Tp_Cleaned", "Eng"]:
        print(f"{lang_code=}")
        subtitles, other_lines = get_subtitles_and_other_lines(lang_code, session_dir, other_lines_already_seen=other_lines)
        if lang_code == "Hk_Cleaned":
            hk_subtitles = [x for x in subtitles]
        elif lang_code == "Tp_Cleaned":
            tp_subtitles = [x for x in subtitles]
        elif lang_code == "Eng":
            eng_subtitles = [x for x in subtitles]
        else:
            raise ValueError(f"{lang_code = }")

    # now interleave subtitles
    for lang_code in ["HkTp", "HkEng"]:
        print(f"{lang_code=}")

        create_srt_interleaved(lang_code, session_dir, hk_subtitles, tp_subtitles, eng_subtitles, other_lines)



if __name__ == "__main__":
    # for aligning the subtitles, pick a segment after you upload the first Horokoi subtitle file and watch the YouTube video with it, find in the subtitle editor where you want it to start (desired_start) vs where it starts in the .srt file (srt_start)
    # do this BEFORE doing the cleaning of Hk and Tp files or translating to English, so that their times will be as desired on YouTube
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
