
import os
from collections import namedtuple

CannedDoc = namedtuple('Document', ['id', 'author', 'author_sort',
                                    'title', 'title_sort', 'year',
                                    'text',])


class CannedLoader(object):

    def __init__(self):
        self._texts = []

    def text(self, identifier):
        """
        Return a single canned text (identified by its numeric identifier)
        """
        if not self._texts:
            self._texts = _load_from_text_file()
        identifier = int(identifier)
        try:
            return self._texts[identifier]
        except KeyError:
            return None

    def iterate(self):
        """
        Iterate though the full list of canned texts
        """
        if not self._texts:
            self._texts = _load_from_text_file()
        # Find the highest value
        highest = max(list(self._texts.keys()))
        for i in range(0, highest + 1):
            doc = self.text(i)
            if doc:
                yield doc


def _load_from_text_file():
    filepath = os.path.join(os.path.dirname(__file__), 'texts.txt')
    lines = []
    with open(filepath) as filehandle:
        for line in filehandle:
            if line.strip():
                lines.append(line.strip())

    sections = []
    for line in lines:
        if line.startswith('-----'):
            sections.append([])
        else:
            sections[-1].append(line)

    texts = {}
    for section in sections:
        identifier = int(section.pop(0).strip('#'))
        doc = CannedDoc(identifier, section.pop(0), section.pop(0),
                        section.pop(0), section.pop(0),
                        int(section.pop(0)), '\n'.join(section),)
        texts[identifier] = doc
    return texts
