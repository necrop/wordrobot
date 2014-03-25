import os
import string
from collections import defaultdict
import pickle
import json
from sys import stdout

import stringtools
from lex.oed.resources.vitalstatistics import VitalStatisticsCache
from lex.oed.resources.mainsenses import MainSensesCache
from apps.tm.build import buildconfig
from .findhtlink import find_htlink

FORM_INDEX_DIR = buildconfig.FORM_INDEX_DIR


def refine_index():
    """
    Refine the data build by index_raw_forms(), in particular removing minor
    homographs (both lemma-level homographs and wordform-level homographs).

    Also swaps in standard lemma forms, main-sense definitions, and
    thesaurus links.
    """
    # Determine which alien variants are okay to keep (because they don't
    #  shadow main forms). - Alien types are wordforms which begin with
    #  a different letter from their parent lemma, and so wouldn't be
    #  correctly filtered by the main letter-by-letter filtering process.
    stdout.write('Filtering alien types...\n')
    allowed_alien_types = _filter_alien_types()
    stdout.write('...done\n')

    # Initialize the resources that will be used for look-ups
    vitalstats = VitalStatisticsCache()
    main_sense_checker = MainSensesCache(with_definitions=True)

    for letter in string.ascii_lowercase:
        stdout.write('Refining index for %s...\n' % letter)
        blocks = []
        for block in _raw_pickle_iterator(letter):
            blocks.append(block)

        # Remove duplicate types, so that only the version
        #  in the block with the highest frequency is retained.
        # Cluster together typeunits with the same wordform + wordclass
        standardmap = defaultdict(lambda: defaultdict(list))
        for i, block in enumerate(blocks):
            for typeunit in block.standard_types:
                standardmap[typeunit.wordform][typeunit.wordclassflat].append(
                    (i, typeunit))
        # Go through each wordclass-cluster for each wordform, and pick
        #  the highest-frequency instance in each case
        for wordform, wordclasses in standardmap.items():
            winners = []
            for candidates in wordclasses.values():
                # Sort by frequency (highest first)
                candidates.sort(key=lambda c: c[1].frequency, reverse=True)
                # Remove the first candidate (the highest-frequency one);
                #  this is the one we'll keep.
                winners.append(candidates.pop(0))
                # Delete all the rest
                for index, typeunit in candidates:
                    blocks[index].standard_types.discard(typeunit)
            # We should now be left with the highest-scoring wordclasses
            #  for the current wordform (e.g. the highest-frequency
            #  homograph for spell_VB and the highest-frequency
            #  homograph for one spell_NN). We now need to decide which
            #  of these to keep and which to discard
            discards = _discardable_homographs(winners)
            for index, typeunit in discards:
                blocks[index].standard_types.discard(typeunit)

        # Remove variant types which either duplicate each other
        #  or that shadow a standard type. (Standard types are always
        #  given precedence.)
        varmap = defaultdict(list)
        for i, block in enumerate(blocks):
            for typeunit in block.variant_types:
                varmap[typeunit.wordform].append((i, typeunit, block.frequency))
        for wordform, candidates in varmap.items():
            if wordform not in standardmap:
                # Sort by the frequency of the parent lemma
                candidates.sort(key=lambda c: c[2], reverse=True)
                # Remove the first candidate (the highest-frequency
                #  one); this is the one we'll keep.
                candidates.pop(0)
            # Delete all the rest
            for index, typeunit, _ in candidates:
                blocks[index].variant_types.discard(typeunit)

        # Remove any alien types that are not allowed (because they
        #  shadow other standard types or variants).
        for block in blocks:
            to_be_deleted = set()
            for typeunit in block.alien_types:
                if typeunit.wordform not in allowed_alien_types:
                    to_be_deleted.add(typeunit)
            for typeunit in to_be_deleted:
                block.alien_types.discard(typeunit)

        # Remove any blocks whose standard_types and
        #  variant_types sets have now been completely emptied
        # For the remainder, turn standard_forms and variant_forms
        #  from sets into lists
        blocks = [_listify_forms(b) for b in blocks if b.standard_types
                  or b.variant_types]

        blocks_filtered = []
        for block in blocks:
            language = vitalstats.find(block.refentry,
                                       field='indirect_language')
            if not language and block.start and block.start < 1200:
                language = 'West Germanic'
            block = _replace_language(block, language)

            # Acquire main-sense data for this block (which will be
            #  used to swap in a new definition and a thesaurus link)
            if block.type == 'entry':
                ms_block_data = main_sense_checker.find_block_data(
                    block.refentry, block.refid)
                if ms_block_data and ms_block_data.senses:
                    main_sense_data = ms_block_data.senses[0]
                    main_sense_confidence = ms_block_data.confidence()
                else:
                    main_sense_data = None
                    main_sense_confidence = None
            else:
                main_sense_data = None
                main_sense_confidence = None

            # Swap in thesaurus-class link
            block = _replace_htclass(block,
                                     main_sense_data,
                                     main_sense_confidence)

            if block.type == 'entry':
                # Make sure we use the OED headword, not the headword
                #  that's been used in GEL (which could be the version
                #  of the headword found in ODE or NOAD).
                headword = vitalstats.find(block.refentry,
                                           field='headword')
                if headword and headword != block.lemma:
                    block = _replace_lemma(block, headword)
                # Make sure we use the best main-sense definition
                if main_sense_data and main_sense_data.definition:
                    block = _replace_definition(block,
                                                main_sense_data.definition)
            blocks_filtered.append(block)

        out_file = os.path.join(FORM_INDEX_DIR, 'refined', letter + '.json')
        with open(out_file, 'w') as filehandle:
            for block in blocks_filtered:
                filehandle.write(json.dumps(block) + '\n')


def _raw_pickle_iterator(letter):
    in_file = os.path.join(FORM_INDEX_DIR, 'raw', letter.lower())
    with open(in_file, 'rb') as filehandle:
        while 1:
            try:
                block = pickle.load(filehandle)
            except EOFError:
                break
            else:
                yield(block)


def _listify_forms(entry):
    return entry._replace(standard_types=list(entry.standard_types),
                          variant_types=list(entry.variant_types),
                          alien_types=list(entry.alien_types))


def _replace_lemma(entry, headword):
    return entry._replace(lemma=headword, sort=stringtools.lexical_sort(headword))


def _replace_definition(entry, definition):
    if definition != entry.definition:
        return entry._replace(definition=definition)
    else:
        return entry


def _replace_language(entry, language):
    if language:
        language = language.split('/')[-1]
    if language == 'English':
        language = 'West Germanic'
    if (entry.start < 1150 and
            (not language or language.lower() in ('unknown', 'undefined', 'origin uncertain'))):
        language = 'West Germanic'
    if (entry.start < 1200 and
            (not language or language.lower() in ('undefined',))):
        language = 'West Germanic'
    return entry._replace(language=language)


def _replace_htclass(block, main_sense_data, confidence):
    link = find_htlink(block, main_sense_data, confidence)
    if link:
        block = block._replace(htlink=link)
    return block


def _filter_alien_types():
    """
    Check which alien types can be kept.
    (Alien types are variants which begin with a different letter from
    the standard lemma form, and which therefore may shadow lemmas
    or variants in other letter sets.)
    """
    # Store all the alien types
    alien_types = set()
    for letter in string.ascii_lowercase:
        for block in _raw_pickle_iterator(letter):
            for t in block.alien_types:
                alien_types.add(t.wordform)

    # Delete any which shadow standard types or other variants (ie. those
    #  which are not aliens, in their own letter sets).
    for letter in string.ascii_lowercase:
        for block in _raw_pickle_iterator(letter):
            for typelist in (block.standard_types, block.variant_types):
                for t in typelist:
                    try:
                        alien_types.discard(t.wordform)
                    except KeyError:
                        pass

    return alien_types


def _discardable_homographs(homographs):
    # Determine which ones will be kept...
    keepers = _evaluate_homographs(homographs)
    # ... and all the others are returned as discards
    return [h for h in homographs if not h in keepers]


def _evaluate_homographs(homographs):
    homographs.sort(key=lambda h: h[1].frequency, reverse=True)
    top_frequency = homographs[0][1].frequency

    # Drop any homographs that are way less frequent than the most frequent
    if top_frequency > 10:
        homographs = [h for h in homographs if
                      h[1].frequency >= top_frequency / 20]
    elif top_frequency > 1:
        homographs = [h for h in homographs if
                      h[1].frequency >= top_frequency / 10]
    elif top_frequency > 0.1:
        homographs = [h for h in homographs if
                      h[1].frequency >= top_frequency / 5]

    # If they're all low-frequency (< 0.1 per million), we just pick the
    #  most frequent of them - it's not worth worrying about these,
    #  and retaining various different homographs will just stuff the Db.
    if len(homographs) == 1 or top_frequency <= 0.1:
        return [homographs[0], ]
    else:
        #print('-----------------------------------------------------')
        #for index, h in homographs[0:3]:
        #    print(h.wordform, h.wordclass, h.wordclassflat, h.frequency)
        return homographs[0:3]
