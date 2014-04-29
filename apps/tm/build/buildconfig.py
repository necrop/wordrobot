"""
buildconfig - configuration for building textmetrics source data

@author: James McCracken
"""

import os

from lex import lexconfig

PIPELINE = (
    ('make_leanht', 0),
    ('inflect_leanht', 0),
    ('populate_leanht_db', 0),
    ('index_proper', 0),
    ('index_forms', 0),
    ('refine_forms', 0),
    ('populate_lexicon_db', 1),
    ('prepare_canned_texts', 1),
)


#============================================================
# Filepaths
#============================================================
BASE_DIR = os.path.join(lexconfig.OED_DIR, 'projects', 'textmetrics')
FORM_INDEX_DIR = os.path.join(BASE_DIR, 'form_index')
LEANHT_DIR = os.path.join(BASE_DIR, 'leanht')

EPONYMS_FILE = os.path.join(BASE_DIR, 'oed_eponyms.txt')

ENTRY_MINIMUM_END_DATE = 1750
VARIANT_MINIMUM_END_DATE = 1650
MAX_WORDLENGTH = 40

LEMMA_FIELDS = ['refentry', 'refid', 'type', 'sort', 'lemma', 'wordclass',
                'definition', 'start', 'end', 'language',
                'htlink', 'standard_types', 'variant_types', 'alien_types',
                'f2000', 'f1950', 'f1900', 'f1850', 'f1800', 'f1750']
TYPE_FIELDS = ['sort', 'wordform', 'wordclass', 'wordclassflat',
               'f2000', 'f1900', 'f1800']

LANGUAGE_FAMILIES = ['Germanic', 'Romance', 'Latin', 'Greek', 'Celtic',
                     'Slavonic', 'African languages',
                     'Native American languages',
                     'Indian subcontinent languages',
                     'Middle Eastern and Afro-Asiatic languages',
                     'Central and Eastern Asian languages',
                     'Australian Aboriginal', 'Austronesian']

# Definitions will only be included for lemmas below this frequency
FREQUENCY_CUTOFF = 10