
import json
import random

from ..models import Document


class DocumentListManager(object):

    """
    Manager for the list of canned documents
    """

    def __init__(self):
        self.documents = Document.objects.all()

    def datastruct(self, **kwargs):
        """
        Turn the list of documents into a JSON data structure, to be
        dumped in the template for the documents library.
        (This will then be composed into a table by javascript.)
        """
        try:
            self._datastruct
        except AttributeError:
            self._datastruct = [doc.to_list() for doc in self.documents]
        if kwargs.get('formalism') == 'json':
            return json.dumps(self._datastruct)
        else:
            return self._datastruct

    def random_list(self, num_items):
        """
        Select a random list of n documents (used for the homepage)

        In fact this is only semi-random: it sorts the list of documents
        by their 'randomsort' attribute, then selects a slice of
        n documents at random.
        """
        qset = Document.objects.all().order_by('randomsort')
        max_rnd = qset.count() - num_items
        start = random.randint(0, max_rnd)
        return qset[start:start + num_items]

    def random_document(self):
        """
        Select a document at random
        """
        qset = Document.objects.all()
        max_rnd = qset.count() - 1
        idx = random.randint(0, max_rnd)
        return qset[idx]
