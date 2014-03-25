
import os

from lxml import etree

from lex.oed.thesaurus.contentiterator import ContentIterator
from lex.inflections.inflection import Inflection
from lex.inflections.mmh.mmhcache import MmhCache
from apps.tm.build import buildconfig
from apps.tm.htmodels import ThesaurusInstance

PARENT_DIR = buildconfig.LEANHT_DIR
IN_DIR = os.path.join(PARENT_DIR, 'iteration2')
OUT_DIR = os.path.join(PARENT_DIR, 'inflected')

MAPPINGS = {'NN': ('NNS',), 'VB': ('VBZ', 'VBG', 'VBD', 'VBN',),}
INFLECTOR = Inflection()
MMH = MmhCache()
INFLECTIONS_LENGTH = ThesaurusInstance._meta.get_field('inflections').max_length


def inflect_ht():
    iterator = ContentIterator(in_dir=IN_DIR, out_dir=OUT_DIR, yield_mode='file')
    for classes in iterator.iterate():
        for thesclass in classes:
            wordclass = thesclass.wordclass(penn=True)
            if wordclass in MAPPINGS:
                for instance in thesclass.instances():
                    z = _get_inflections(instance.lemma(), wordclass)
                    if z:
                        inf_node = etree.SubElement(instance.node, 'infl')
                        inf_node.text = z


def _get_inflections(lemma, wordclass):
    inflections = []
    morphsets = MMH.inflect_fuzzy(lemma, wordclass=wordclass, locale='uk')
    if morphsets:
        for u in [u for u in morphsets[0].morphunits
                  if u.wordclass in MAPPINGS[wordclass]]:
            inflections.append((u.form, u.wordclass))
    else:
        inflections = _compute_inflections(lemma, wordclass)

    infstring = ''
    for inflection in inflections:
        infstring_new = infstring + '%s=%s' % (inflection[1], inflection[0])
        if len(infstring_new) > INFLECTIONS_LENGTH:
            break
        else:
            infstring = infstring_new + '|'
    return infstring.strip('|')


def _compute_inflections(lemma, wordclass):
    inflections = []
    num_words = len(lemma.split())
    # Don't attempt to inflect long phrases
    if num_words <= 2:
        for inf in MAPPINGS[wordclass]:
            inflected_form = INFLECTOR.compute_inflection(lemma,
                                                          inf,
                                                          archaic=False)
            inflections.append((inflected_form, inf))
    return inflections
