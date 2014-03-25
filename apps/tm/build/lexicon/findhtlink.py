__author__ = 'james'

import stringtools
from apps.tm.htmodels import ThesaurusInstance

BANNED_LEMMAS = set(('have', 'like', 'be', 'make', 'do', 'set', 'put',
    'go', 'get', 'take', 'will', 'right', 'let'))
ALLOWED_ADVERBS = set(('perhaps', 'maybe', 'however', 'therefore', 'often',
    'sometimes', 'almost', 'today', 'yesterday', 'tomorrow', 'forever',
    'always', 'together', 'indeed', 'tonight', 'alone', 'never'))


def find_htlink(block, main_sense_data, confidence):
    if confidence is not None and confidence <= 2:
        #print(block.lemma, block.wordclass, confidence)
        return None
    if block.lemma in BANNED_LEMMAS:
        return None
    if block.wordclass not in ('NN', 'VB', 'JJ', 'RB', 'UH'):
        return None
    if (block.wordclass == 'RB' and
            not block.lemma.endswith('ly') and
            not block.lemma.endswith('wise') and
            not block.lemma.endswith('ways') and
            not block.lemma in ALLOWED_ADVERBS):
        return None

    if block.type == 'entry' and main_sense_data:
        main_sense = (block.refentry, main_sense_data.sense_id)
    elif block.type != 'entry':
        main_sense = (block.refentry, block.refid)
    else:
        main_sense = None

    if main_sense:
        qset = ThesaurusInstance.objects.filter(refentry=main_sense[0],
                                                refid=main_sense[1])
        # Double-check that these are the right p.o.s...
        records = [r for r in qset if r.wordclass() == block.wordclass]
        # ...and roughly the right lemma
        records = ([r for r in records if r.lemma == block.lemma] or
                   [r for r in records if stringtools.lexical_sort(r.lemma) == block.sort])
        # sort so the record from the largest set is top
        records.sort(key=lambda r: r.thesclass.branch_size, reverse=True)
        if records and records[0].thesclass.node_size >= 3:
            return int(records[0].thesclass.id)

    return None