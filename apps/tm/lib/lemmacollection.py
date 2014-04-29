
class LemmaCollection(object):

    def __init__(self, tokens):
        self._lemmas = _collate_lemmas(tokens)

    def __len__(self):
        return len(self.lemmas())

    def count(self):
        return len(self.lemmas())

    def lemmas(self):
        return list(self._lemmas.values())

    def add_counts_to_tokens(self, tokens):
        for token in [t for t in tokens if t.is_in_oed()]:
            identifier = token.oed_identifier()
            token.count = self._lemmas[identifier].count

    def rank_by_general_frequency(self):
        rank = self.lemmas()
        rank.sort(key=lambda l: l.sort)
        rank.sort(key=lambda l: l.f2000, reverse=True)
        return rank

    def rank_by_document_frequency(self):
        rank = self.lemmas()
        rank.sort(key=lambda l: l.sort)
        rank.sort(key=lambda l: l.count, reverse=True)
        return rank

    def rank_by_year(self):
        rank = self.lemmas()
        rank.sort(key=lambda l: l.sort)
        rank.sort(key=lambda l: l.firstyear)
        return rank

    def datastruct(self):
        lemma_struct = []
        for lemma in self.rank_by_document_frequency():
            lemma_struct.append(lemma.to_list())
        return lemma_struct


def _collate_lemmas(tokens):
    """
    Collect up all the lemmas attached to tokens; count the number of
    tokens attached to each lemma (as the .count attribute); map all
    in the 'lemmas' dictionary (key=oed identifier, value=lemma).
    """
    lemmas = {}
    for token in [t for t in tokens if t.is_in_oed()]:
        identifier = token.oed_identifier()
        if identifier in lemmas:
            lemmas[identifier].count += 1
        else:
            lemmas[identifier] = token.lemma_manager()
            lemmas[identifier].count = 1

    return lemmas
