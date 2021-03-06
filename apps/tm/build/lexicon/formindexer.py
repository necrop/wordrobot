"""
FormIndexer

@author: James McCracken
"""

import os
import string
from collections import namedtuple, defaultdict
import pickle
from sys import stdout

import stringtools
from lex.gel.fileiterator import entry_iterator
from apps.tm.build import buildconfig

FORM_INDEX_DIR = buildconfig.FORM_INDEX_DIR
ENTRY_MINIMUM_END_DATE = buildconfig.ENTRY_MINIMUM_END_DATE
VARIANT_MINIMUM_END_DATE = buildconfig.VARIANT_MINIMUM_END_DATE
MAX_WORDLENGTH = buildconfig.MAX_WORDLENGTH
LEMMA_FIELDS = buildconfig.LEMMA_FIELDS
TYPE_FIELDS = buildconfig.TYPE_FIELDS

BlockData = namedtuple('BlockData', LEMMA_FIELDS)
TypeData = namedtuple('TypeData', TYPE_FIELDS)


def index_raw_forms():
    """
    Build an index of all OED lemmas and their various inflections/variants.
    Based on GEL.
    Outputs a series of pickle files (one file per letter).
    """
    for letter in string.ascii_lowercase:
        stdout.write('Indexing %s...\n' % letter)
        blocks = []
        for entry in entry_iterator(letters=letter):
            # Skip proper names and over-long lemmas
            if (entry.date().end < ENTRY_MINIMUM_END_DATE or
                    entry.primary_wordclass() in ('NP', 'NPS') or
                    len(entry.lemma) > MAX_WORDLENGTH):
                continue

            entry_type = entry.oed_entry_type()
            if entry_type is None:
                continue
            seen = set()
            for block in entry.wordclass_sets():
                # Check that this block is in OED, and does not shadow
                #  something already covered within this entry
                # (as e.g. _vast_ adv. shadows _vast_ adj.).
                refentry, refid = block.link(target='oed', asTuple=True)
                if not refentry or (refentry, refid) in seen:
                    continue
                block_data = _store_forms(block, entry, entry_type, letter)
                if block_data.standard_types:
                    blocks.append(block_data)
                seen.add((refentry, refid))

        out_file = os.path.join(FORM_INDEX_DIR, 'raw', letter)
        with open(out_file, 'wb') as filehandle:
            for block in blocks:
                pickle.dump(block, filehandle)


def _store_forms(block, entry, block_type, letter):
    us_variant = entry.us_variant()
    standardtypes = set()
    varianttypes = set()
    alientypes = set()
    for morphset in block.morphsets():
        if (morphset.form in (entry.lemma, us_variant, block.lemma) or
                morphset.is_oed_headword()):
            _add_types(morphset, standardtypes, letter)
        elif (block_type == 'entry' and
                morphset.date().end > VARIANT_MINIMUM_END_DATE and
                not morphset.is_nonstandard()):
            # Don't store variants for subentries; don't store
            #  very old or non-standard variants
            _add_types(morphset, varianttypes, letter)
            _add_alien_variants(morphset, alientypes, letter)
    varianttypes = varianttypes - standardtypes
    alientypes = alientypes - standardtypes

    refentry, refid = block.link(target='oed', asTuple=True)

    if block.has_frequency_table():
        f2000 = block.frequency_table().frequency(period='1990-2007')
        f1950 = block.frequency_table().frequency(period='1940-1959')
        f1900 = block.frequency_table().frequency(period='1890-1909')
        f1850 = block.frequency_table().frequency(period='1840-1859')
        f1800 = block.frequency_table().frequency(period='1790-1809')
        f1750 = block.frequency_table().frequency(period='1750-1769')
    else:
        f2000 = 0
        f1950 = 0
        f1900 = 0
        f1850 = 0
        f1800 = 0
        f1750 = 0

    definition = block.definition(src='oed') or None

    return BlockData(refentry,
                     refid,
                     block_type,
                     stringtools.lexical_sort(block.lemma),
                     block.lemma,
                     block.wordclass(),
                     definition,
                     block.date().exact('start'),
                     block.date().exact('end'),
                     None,
                     None,
                     standardtypes,
                     varianttypes,
                     alientypes,
                     _round_number(f2000),
                     _round_number(f1950),
                     _round_number(f1900),
                     _round_number(f1850),
                     _round_number(f1800),
                     _round_number(f1750),)


def _add_types(morphset, target_set, letter):
    # Check if (in the case of a verb) the VBN and VBD forms are the same;
    # we'll flatten them to a single form if so
    duplicate_pasts = False
    pastforms = set([typeunit.form for typeunit in morphset.types()
                     if typeunit.wordclass() in ('VBN', 'VBD')])
    if len(pastforms) == 1:
        duplicate_pasts = True

    typelist = []
    for typeunit in morphset.types():
        if (len(typeunit.sort) > MAX_WORDLENGTH or
                len(typeunit.form) > MAX_WORDLENGTH or
                not typeunit.sort.startswith(letter)):
            pass
        else:
            typelist.append(_compile_type_data(typeunit, duplicate_pasts))

    # Deduplicate, keeping the version with the highest frequency (and adding
    #  the frequency score of the loser to that of the winner)
    # Cluster into groups sharing the same wordform...
    clusters = defaultdict(list)
    for typeunit in typelist:
        clusters[typeunit.wordform].append(typeunit)
    # ...and pick the one with the highest frequency (giving it the sum
    #   of all the frequencies)
    for cluster in clusters.values():
        total_f2000 = sum([t.f2000 for t in cluster])
        total_f1900 = sum([t.f1900 for t in cluster])
        total_f1800 = sum([t.f1800 for t in cluster])
        cluster.sort(key=lambda t: t.f2000, reverse=True)
        new_typeunit = cluster[0]._replace(f2000=total_f2000,
                                           f1900=total_f1900,
                                           f1800=total_f1800)
        target_set.add(new_typeunit)


def _add_alien_variants(morphset, target_set, letter):
    """
    Store variants that start with a letter *other* than the current
    letter (e.g. 'cimiter' under 'scimitar').
    """
    for typeunit in morphset.types():
        if (len(typeunit.sort) > MAX_WORDLENGTH or
                len(typeunit.form) > MAX_WORDLENGTH or
                typeunit.sort.startswith(letter)):
            pass
        else:
            target_set.add(_compile_type_data(typeunit, False))


def _compile_type_data(type_unit, duplicate_pasts):
    # For the purposes of filtering, we can treat some wordclasses
    #   as essentially interchangeable; so these get flattened to
    #   the 'wordclassflat' attribute, which is what gets used in the
    #   refine stage
    wordclass = type_unit.wordclass()
    # If there's both a VBN and a VBD, and these are identical,
    #  we flatten them to a hybrid VBND
    if wordclass in ('VBN', 'VBD') and duplicate_pasts:
        wordclass = 'VBND'
    wordclassflat = wordclass

    if wordclassflat == 'NNS':
        wordclassflat = 'NN'
    elif wordclassflat in ('VBD', 'VBN', 'VBND'):
        wordclassflat = 'VBND'
    elif wordclassflat in ('RB', 'CC', 'IN', 'PP'):
        wordclassflat = 'JJ'
    elif wordclassflat == 'MD':
        wordclassflat = 'VB'
    elif wordclassflat in ('JJR', 'JJS'):
        wordclassflat = 'JJ'
    elif wordclassflat in ('RB', 'RBR', 'RBS'):
        wordclassflat = 'JJ'

    if type_unit.has_frequency_table():
        f2000 = type_unit.frequency_table().frequency(period='1980-2007')
        f1900 = type_unit.frequency_table().frequency(period='1880-1919')
        f1800 = type_unit.frequency_table().frequency(period='1780-1819')
    else:
        f2000 = 0
        f1900 = 0
        f1800 = 0

    return TypeData(type_unit.sort,
                    type_unit.form,
                    wordclass,
                    wordclassflat,
                    _round_number(f2000),
                    _round_number(f1900),
                    _round_number(f1800))


def _round_number(n):
    if n > 1:
        n = int(n)
    else:
        n = float('%.2g' % n)
    return n
