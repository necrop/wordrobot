

import re
from unidecode import unidecode
from functools import lru_cache

DIGIT_TRANSLATOR = (
    ('0', 'zero'),
    ('1', 'one'),
    ('2', 'two'),
    ('3', 'three'),
    ('4', 'four'),
    ('5', 'five'),
    ('6', 'six'),
    ('7', 'seven'),
    ('8', 'eight'),
    ('9', 'nine'),)

LETTERS_ONLY = re.compile(r'[^a-z]')


@lru_cache(maxsize=512)
def lexicalsort(text):
    text = unidecode(text.lower())
    for before, after in DIGIT_TRANSLATOR:
        text = text.replace(before, after)
    text = LETTERS_ONLY.sub('', text)
    return text
