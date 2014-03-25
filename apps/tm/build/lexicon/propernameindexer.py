from sys import stdout
import os
import string

import stringtools
from lex.gel.fileiterator import entry_iterator
from lex.propernames import propernames
from apps.tm.build import buildconfig

FORM_INDEX_DIR = buildconfig.FORM_INDEX_DIR
MAX_WORDLENGTH = buildconfig.MAX_WORDLENGTH


def index_proper_names():
    allnames = set()
    for name_type in ('firstname', 'surname', 'placename'):
        for name in propernames.names_list(name_type):
            if ' ' in name:
                continue
            allnames.add(name)

    for letter in string.ascii_lowercase:
        stdout.write('Indexing proper names in %s...\n' % letter)
        for entry in entry_iterator(letters=letter):
            if entry.primary_wordclass() not in ('NP', 'NPS'):
                continue
            for typeunit in entry.types():
                if (' ' in typeunit.form or
                    not typeunit.lemma_manager().capitalization_type() == 'capitalized'):
                    continue
                allnames.add(typeunit.form)

    out_file = os.path.join(FORM_INDEX_DIR, 'proper_names', 'all.txt')
    with open(out_file, 'w') as filehandle:
        for name in allnames:
            sortable = stringtools.lexical_sort(name)
            if (not sortable or
                    len(sortable) > MAX_WORDLENGTH or
                    len(name) > MAX_WORDLENGTH):
                continue
            filehandle.write('%s\t%s\t%s\n' % (sortable,
                                               name,
                                               str(propernames.is_common(name))))