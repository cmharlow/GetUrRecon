import re
import pymarc


def dates_parse(label):
    creator_raw = label
    if re.match('.+\d+)', creator_raw):
        creator = re.sub(',?.?\d+\s?-{1}\d{0,}', '', creator_raw)
        return creator
    else:
        return label


def name_alone(field):
    field = pymarc.Field()
    label = field.value()
    label_4 = label.replace(str(field['4']), '').strip()
    label_e = label_4.replace(str(field['e']), '').strip()
    label_fin = label_e.strip(',')
    label_fin2 = label_fin.strip('.')
    return(label_fin2)
