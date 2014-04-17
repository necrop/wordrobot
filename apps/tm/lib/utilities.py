
import re

APOSTROPHE_MASK = 'ZAPOSZ'
APOSTROPHE_MASKER1 = re.compile(r"(..[bcdfghjklmnprstvwxz])'d([ ,.:;)]|$)")
APOSTROPHE_MASKER2 = re.compile(r"(..[bcdfghjklmnprstvwxz])in'([ ,.:;)]|$)")
APOSTROPHE_MASKER3 = re.compile(r"(^| )([Gg]o|[Ss]ee|[Dd]o)in'([ ,.:;)]|$)")
STOP_MASK = 'ZSTOPZ'
STOP_MASKER = re.compile(r"(Mr|Mrs|Ms|Messrs|Capt|Ld|Revd|Bp| [A-Z])\. ([A-Z][a-z.]|O')")


def json_safe(text):
    return text.replace('"', '&quot;').replace("'", '&apos;')


def apostrophe_masker(text, year):
    """
    Mask apostrophes in archaic spelling (pass'd, touch'd etc.),
    so that they don't get erroneously split by the tokenizer.

    But note that when the 'd is a shortening of 'had' or 'would'
    (e.g. in I'd, they'd, we'd), we *do* want to split into
    two tokens, so the apostrophe is left unmasked.
    """
    if year < 1900:
        text = APOSTROPHE_MASKER1.sub(r'\1' + APOSTROPHE_MASK + r'd\2', text)
    if year > 1950:
        text = APOSTROPHE_MASKER2.sub(r'\1in' + APOSTROPHE_MASK + r'\2', text)
        text = APOSTROPHE_MASKER3.sub(r'\1\2in' + APOSTROPHE_MASK + r'\3', text)
    return text


def apostrophe_unmasker(text):
    return text.replace(APOSTROPHE_MASK, "'")


def stop_masker(text):
    text = STOP_MASKER.sub(r'\1' + STOP_MASK + r' \2', text)
    return text


def stop_unmasker(text):
    return text.replace(STOP_MASK, '.')