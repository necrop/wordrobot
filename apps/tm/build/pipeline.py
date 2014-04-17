"""
pipeline -- runs processes for building data for the text metrics app.
Controlled by settings in buildconfig.py

@author: James McCracken
"""

from sys import stdout

from apps.tm.build import buildconfig


def dispatch():
    for function_name, status in buildconfig.PIPELINE:
        if status:
            stdout.write('=' * 30 + '\n')
            stdout.write('Running "%s"...\n' % function_name)
            stdout.write('=' * 30 + '\n')
            function = globals()[function_name]
            function()


def make_leanht():
    from apps.tm.build.leanht.makeleanht import make_lean_ht
    make_lean_ht()


def inflect_leanht():
    from apps.tm.build.leanht.inflectht import inflect_ht
    inflect_ht()


def populate_leanht_db():
    from apps.tm.build.leanht.populatedb import store_content, store_taxonomy
    store_taxonomy()
    store_content()


def index_proper():
    from apps.tm.build.lexicon.propernameindexer import index_proper_names
    index_proper_names()


def index_forms():
    from apps.tm.build.lexicon.formindexer import index_raw_forms
    index_raw_forms()


def refine_forms():
    from apps.tm.build.lexicon.refiner import refine_index
    refine_index()


def populate_lexicon_db():
    from apps.tm.build.lexicon.populatedb import populate_db
    populate_db()


def prepare_canned_texts():
    from apps.tm.build.canned.preparecannedtexts import prepare_canned_texts
    prepare_canned_texts()
