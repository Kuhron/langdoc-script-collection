import os
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List

import util.Correlation as cor
from util.VideoAudioAligningOrganization import get_tmp_dir_path
from util.CliUtil import confirm_action



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


def write_texts_interleaved(target_lang_texts: List[str], contact_lang_texts: List[str], output_fp: Path):
    assert len(target_lang_texts) == len(contact_lang_texts)
    with open(output_fp, "w") as f:
        for i in range(len(target_lang_texts)):
            ts = target_lang_texts[i]
            cs = contact_lang_texts[i]
            f.write(f"{i+1}.\nTranscription: {ts}\nTranslation: {cs}\n----\n")


def get_texts_and_times_from_eaf(fp: Path):
    assert fp.suffix == ".eaf", f"{fp} is not a .eaf file"

    targlang_texts = []
    contlang_texts = []
    start_times = []
    end_times = []

    tree = ET.parse(fp)
    root = tree.getroot()
    # target language is the TIER with LINGUISTIC_TYPE_REF="Transcription"
    # contact language is the TIER with LINGUISTIC_TYPE_REF="Translation"
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
            targlang_text = ""
        elif targlang_text is None:
            targlang_text = ""
        targlang_by_annotation_id[annotation_id] = targlang_text

    # the other tier has a different structure in the XML
    contlang_annotation_els = contlang_tier_el.findall("ANNOTATION")
    for el in contlang_annotation_els:
        ref_el, = el.findall("REF_ANNOTATION")
        annotation_id = ref_el.attrib["ANNOTATION_REF"]
        # THIS annotation, the contact-language one, is ANNOTATION_ID, but we want to match it with the corresponding target-language text, which is ANNOTATION_REF
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


def create_interleaved_text_file_from_eaf(text_dir: Path):
    eaf_fp = get_existing_eaf_fp_from_text_dir(text_dir)
    target_lang_texts, contact_lang_texts, start_times, end_times = get_texts_and_times_from_eaf(eaf_fp)
    output_fp = text_dir / "InterleavedText.txt"
    write_texts_interleaved(target_lang_texts, contact_lang_texts, output_fp)
    print(f"\nInterleaved text file has been created at {output_fp}.\nPlease edit the text strings as desired, because these will be used to create the subtitle files.")


def get_existing_eaf_fp_from_text_dir(text_dir: Path, prompt_if_not_aligned:bool=False):
    eaf_ext = ".eaf"
    eaf_fps = list(text_dir.glob("*" + eaf_ext))
    eaf_aligned_fps = list(text_dir.glob("*_aligned" + eaf_ext))

    if len(eaf_aligned_fps) == 1:
        eaf_fp ,= eaf_aligned_fps
    elif len(eaf_aligned_fps) > 1:
        raise Exception(f"there should be no more than one aligned .eaf transcript file in the directory")
    else:
        if prompt_if_not_aligned:
            confirmed = confirm_action(f"\nWarning: there are no .eafs that are labeled as having been aligned with the video file (the .eaf should end in '_aligned.eaf'). Are you sure you have the right file?")
            if not confirmed:
                raise Exception("aborted")
        if len(eaf_fps) == 1:
            eaf_fp ,= eaf_fps
        else:
            raise Exception(f"since you have no aligned .eaf transcript, there should be exactly one .eaf transcript file in the directory")

    return eaf_fp

