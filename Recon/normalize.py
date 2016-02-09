import re


def dates_parse(label):
    creator_raw = label
    if re.match('.+\d+)', creator_raw):
        creator = re.sub(',?.?\d+\s?-{1}\d{0,}', '', creator_raw)
        return creator
    else:
        return label
