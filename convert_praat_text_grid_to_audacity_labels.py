import re


input_fp = "Praat/ZOOM0050_TrLR.TextGrid"
output_fp = "Praat/ZOOM0050_TrLR_AudacityLabels.txt"

# Audacity label file format is one line per label, each line is f"{start_time_seconds}\t{end_time_seconds}\t{label text}"

with open(input_fp, encoding="utf-16") as f:
    lines = f.readlines()

desired_tier_name = "word"
tier_name_line_re = f"        name = \"{desired_tier_name}\""
item_line_re = r"    item \[(?P<item_number>\d+)\]:"
interval_line_re = r"        intervals \[(?P<interval_number>\d+)\]:"
inside_interval_re = " " * 12 + "(?P<var>\w+) = (?P<val>[^\n]+)"

# get every interval line and associated data below it, starting from the correct tier name line and ending with the next item line (a different tier)

intervals = {}

in_correct_tier = False
interval_number = None
current_interval_dict = None
for line in lines:
    if re.match(tier_name_line_re, line):
        in_correct_tier = True
    elif re.match(item_line_re, line):
        in_correct_tier = False
    if not in_correct_tier:
        continue

    interval_match = re.match(interval_line_re, line)
    if interval_match:
        if current_interval_dict is not None:
            # assign the currently accumulated info to the previous interval number before updating the interval number
            intervals[interval_number] = current_interval_dict
        interval_number = int(interval_match["interval_number"])
        current_interval_dict = {}
    inside_interval_match = re.match(inside_interval_re, line)
    if inside_interval_match:
        var = inside_interval_match["var"]
        val = inside_interval_match["val"]
        current_interval_dict[var] = val


# now get the intervals with non-empty text
interval_numbers = sorted(intervals.keys())
interval_numbers_to_keep = []
for n in interval_numbers:
    iv = intervals[n]
    text = iv["text"].strip()
    # first strip off the spaces outside the quotes, then remove the quotes, then strip again to see if there is any real content
    assert text[0] == text[-1] == "\"", text
    text_no_quotes = text[1:-1]
    text_stripped = text_no_quotes.strip()
    if text_stripped != "":
        interval_numbers_to_keep.append(n)
        intervals[n]["text_no_quotes"] = text_no_quotes

label_file_contents = ""
for n in interval_numbers_to_keep:
    iv = intervals[n]
    start = float(iv["xmin"])
    end = float(iv["xmax"])
    text = iv["text_no_quotes"]
    # Audacity labels don't allow certain characters: * ? \ / : " < > |
    text = text.replace("\"\"", "_").replace("\"", "_")
    text = re.sub(r"[\*\?\\\/\:\"\<\>\|]", "_", text)
    label_file_line = f"{start:.6f}\t{end:.6f}\t{text}"
    # maybe the label file is forced to have microseconds only (Praat gives way more digits for some reason); yep, that was it
    print(label_file_line)
    label_file_contents += label_file_line + "\n"

with open(output_fp, "w") as f:
    f.write(label_file_contents)
