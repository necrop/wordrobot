"""
Populate the Document database table with canned documents
"""

from sys import stdout
import random

from apps.tm.build.canned.cannedloader import CannedLoader
from apps.tm.models import Document
from apps.tm.lib.textmanager import TextManager


def prepare_canned_texts():
    """
    Load the list of documents from the text file, process them,
    and save the results as canned JSON objects in the Document database.
    """
    # Truncate the existing Document database table
    Document.objects.all().delete()

    canned_loader = CannedLoader()
    for doc in canned_loader.iterate():
        # Process this document
        tm = TextManager(doc.text, doc.year)
        # Trace progress message
        stdout.write('%s, %s\n' % (doc.author, doc.title))

        # Trim fields where necessary
        mlength = Document._meta.get_field('author').max_length
        author = doc.author[:mlength]

        mlength = Document._meta.get_field('authorsort').max_length
        author_sort = doc.author_sort[:mlength]

        mlength = Document._meta.get_field('title').max_length
        title = doc.title[:mlength]

        mlength = Document._meta.get_field('titlesort').max_length
        title_sort = doc.title_sort[:mlength]

        # Prepare database record for this document
        dbdoc = Document(author=author,
                         authorsort=author_sort,
                         title=title,
                         titlesort=title_sort,
                         year=doc.year,
                         teaser=tm.teaser(),
                         text=tm.text,
                         lemmas=tm.lemmas_datastruct(formalism='json'),
                         tokens=tm.tokens_datastruct(formalism='json'),
                         randomsort=random.randint(0, 1000),)
        # Save the database record
        dbdoc.save()
