import os
from sys import stdout
import re

from lex.oed.thesaurus.contentiterator import ContentIterator
from lex.oed.thesaurus.taxonomymanager import TaxonomyManager
from apps.tm.htmodels import ThesaurusInstance, ThesaurusClass
from apps.tm.build import buildconfig

IN_DIR = os.path.join(buildconfig.LEANHT_DIR, 'inflected')
LABEL_LENGTH = ThesaurusClass._meta.get_field('label').max_length


def store_taxonomy():
    ThesaurusInstance.objects.all().delete()
    ThesaurusClass.objects.all().delete()

    ci = ContentIterator(in_dir=IN_DIR, fixLigatures=True, verbosity='low')
    valid_ids = {thesclass.id(): thesclass.size()
                 for thesclass in ci.iterate()}

    tree_manager = TaxonomyManager(lazy=True, verbosity=None)
    for level in range(1, 20):
        classes = [c for c in tree_manager.classes if c.level() == level
                   and c.id() in valid_ids]
        stdout.write('%d\t%d\n' % (level, len(classes)))
        records = []
        for thesclass in classes:
            revised_size = valid_ids[thesclass.id()]
            if thesclass.label():
                label = thesclass.label()[0:LABEL_LENGTH]
            else:
                label = None
            record = ThesaurusClass(id=thesclass.id(),
                                    label=label,
                                    wordclass=thesclass.wordclass(penn=True),
                                    level=thesclass.level(),
                                    parent_id=thesclass.parent(),
                                    node_size=revised_size,
                                    branch_size=thesclass.size(branch=True))
            records.append(record)
            if len(records) > 1000:
                ThesaurusClass.objects.bulk_create(records)
                records = []
        ThesaurusClass.objects.bulk_create(records)


def store_content():
    ThesaurusInstance.objects.all().delete()

    ci = ContentIterator(in_dir=IN_DIR, fixLigatures=True, verbosity='low')
    records = []
    for thesclass in ci.iterate():
        for instance in thesclass.instances():
            inf_node = instance.node.find('./infl')
            if inf_node is not None:
                inflections = inf_node.text or None
            else:
                inflections = None
            record = ThesaurusInstance(lemma=instance.lemma(),
                                       refentry=instance.refentry(),
                                       refid=instance.refid(),
                                       start_year=instance.start_date(),
                                       end_year=instance.end_date(),
                                       thesclass_id=thesclass.id(),
                                       inflections=inflections,)
            records.append(record)
        if len(records) > 1000:
            ThesaurusInstance.objects.bulk_create(records)
            records = []
    ThesaurusInstance.objects.bulk_create(records)
