import os
import string
import json
from collections import namedtuple
from sys import stdout

from lex.oed.languagetaxonomy import LanguageTaxonomy
from apps.tm.models import Lemma, Wordform, Definition, Language, ProperName
from apps.tm.build import buildconfig

LEMMA_FIELDS = buildconfig.LEMMA_FIELDS
BlockData = namedtuple('BlockData', LEMMA_FIELDS)


def populate_db():
    """
    Populate the database table for Language, Lemma, Wordform, and Definition
    """
    stdout.write('Emptying the tables...\n')
    empty_tables()
    stdout.write('Populating Language records...\n')
    populate_language()
    stdout.write('Populating Lemma, Wordform, and Definition records...\n')
    populate_lexical()
    stdout.write('Populating ProperName records...\n')
    populate_proper_names()


def empty_tables():
    """
    Empty the database tables of any existing content
    """
    Wordform.objects.all().delete()
    Lemma.objects.all().delete()
    Definition.objects.all().delete()
    Language.objects.all().delete()
    ProperName.objects.all().delete()


def populate_language():
    """
    Populate the Language table
    """
    taxonomy = LanguageTaxonomy()
    taxonomy.families = set(buildconfig.LANGUAGE_FAMILIES)

    max_length = Language._meta.get_field('name').max_length

    language_objects = []
    for language in taxonomy.languages():
        name = language.name[:max_length]
        language_objects.append(Language(id=language.id, name=name, family=None))
    Language.objects.bulk_create(language_objects)

    for language in taxonomy.languages():
        family = taxonomy.family_of(language.name)
        if family is not None:
            src = Language.objects.get(id=language.id)
            target = Language.objects.get(id=family.id)
            src.family = target
            src.save()


def populate_lexical():
    """
    Populate the Lemma, Wordform, and Definition tables
    """
    in_dir = os.path.join(buildconfig.FORM_INDEX_DIR, 'refined')
    frequency_cutoff = buildconfig.FREQUENCY_CUTOFF

    taxonomy = LanguageTaxonomy()
    lemma_counter = 0
    definition_counter = 0

    for letter in string.ascii_lowercase:
        stdout.write('Inserting data for %s...\n' % letter)
        blocks = []
        in_file = os.path.join(in_dir, letter + '.json')
        with open(in_file, 'r') as filehandle:
            for line in filehandle:
                data = json.loads(line.strip())
                blocks.append(BlockData(*data))

        lemmas = []
        wordforms = []
        definitions = []
        for i, block in enumerate(blocks):
            lang_node = taxonomy.node(language=block.language)
            if lang_node is None:
                language_id = None
            else:
                language_id = lang_node.id

            if block.definition and block.f2000 < frequency_cutoff:
                definition_counter += 1
                definitions.append(Definition(id=definition_counter,
                                              text=block.definition[:100]))
                definition_id = definition_counter
            else:
                definition_id = None

            lemma_counter += 1
            lemmas.append(Lemma(id=lemma_counter,
                                lemma=block.lemma,
                                sort=block.sort,
                                wordclass=block.wordclass,
                                firstyear=block.start,
                                lastyear=block.end,
                                refentry=block.refentry,
                                refid=block.refid,
                                thesaurus_id=block.htlink,
                                language_id=language_id,
                                definition_id=definition_id,
                                f2000=_rounder(block.f2000),
                                f1950=_rounder(block.f1950),
                                f1900=_rounder(block.f1900),
                                f1850=_rounder(block.f1850),
                                f1800=_rounder(block.f1800),
                                f1750=_rounder(block.f1750),))

            for typelist in (block.standard_types,
                             block.variant_types,
                             block.alien_types):
                for typeunit in typelist:
                    wordforms.append(Wordform(sort=typeunit[0],
                                              wordform=typeunit[1],
                                              wordclass=typeunit[2],
                                              lemma_id=lemma_counter,
                                              f2000=_rounder(typeunit[4]),
                                              f1900=_rounder(typeunit[5]),
                                              f1800=_rounder(typeunit[6]),))

            if i % 1000 == 0:
                Definition.objects.bulk_create(definitions)
                Lemma.objects.bulk_create(lemmas)
                Wordform.objects.bulk_create(wordforms)
                definitions = []
                lemmas = []
                wordforms = []

        Definition.objects.bulk_create(definitions)
        Lemma.objects.bulk_create(lemmas)
        Wordform.objects.bulk_create(wordforms)


def populate_proper_names():
    """
    Populate the ProperName table
    """
    in_dir = os.path.join(buildconfig.FORM_INDEX_DIR, 'proper_names')
    in_file = os.path.join(in_dir, 'all.txt')
    names = []
    counter = 0
    with open(in_file) as filehandle:
        for line in filehandle:
            data = line.strip().split('\t')
            if len(data) == 3:
                counter += 1
                sortable, name, common = data
                if common.lower() == 'true':
                    common = True
                else:
                    common = False

                names.append(ProperName(lemma=name,
                                        sort=sortable,
                                        common=common))
                if counter % 1000 == 0:
                    ProperName.objects.bulk_create(names)
                    names = []

    ProperName.objects.bulk_create(names)


def _rounder(n):
    n = float('%.2g' % n)
    if n == 0 or n > 1:
        return int(n)
    else:
        return n
