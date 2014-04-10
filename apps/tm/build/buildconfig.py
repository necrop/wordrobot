"""
buildconfig - configuration for building textmetrics source data

@author: James McCracken
"""

import os

from lex import lexconfig

PIPELINE = (
    ('make_leanht', 1),
    ('inflect_leanht', 1),
    ('populate_leanht_db', 1),
    ('index_proper', 1),
    ('index_forms', 1),
    ('refine_forms', 1),
    ('populate_lexicon_db', 1),
    ('prepare_canned_texts', 1),
    ('prepare_full_text_stats', 0)
)


#============================================================
# Filepaths
#============================================================
BASE_DIR = os.path.join(lexconfig.OED_DIR, 'projects', 'textmetrics')
FORM_INDEX_DIR = os.path.join(BASE_DIR, 'form_index')
LEANHT_DIR = os.path.join(BASE_DIR, 'leanht')


ENTRY_MINIMUM_END_DATE = 1750
VARIANT_MINIMUM_END_DATE = 1650
MAX_WORDLENGTH = 40

LEMMA_FIELDS = ['refentry', 'refid', 'type', 'sort', 'lemma', 'wordclass',
                'definition', 'frequency', 'start', 'end', 'language',
                'htlink', 'standard_types', 'variant_types', 'alien_types']
TYPE_FIELDS = ['sort', 'wordform', 'wordclass', 'wordclassflat', 'frequency']

LANGUAGE_FAMILIES = ['Germanic', 'Romance', 'Latin', 'Greek', 'Celtic',
                     'Slavonic', 'African languages',
                     'Native American languages',
                     'Indian subcontinent languages',
                     'Middle Eastern and Afro-Asiatic languages',
                     'Central and Eastern Asian languages',
                     'Australian Aboriginal', 'Austronesian']

# Definitions will only be included for lemmas below this frequency
FREQUENCY_CUTOFF = 10