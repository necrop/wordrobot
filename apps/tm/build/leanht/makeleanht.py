
import re
import os
from collections import defaultdict

from lex import lexconfig
from lex.oed.thesaurus.contentiterator import ContentIterator
from lex.oed.resources.mainsenses import MainSensesCache
from apps.tm.htmodels import ThesaurusInstance
from apps.tm.build import buildconfig
from stringtools import lexical_sort

MAIN_SENSE_CHECKER = MainSensesCache()
IN_DIR = lexconfig.HTOED_CONTENT_DIR
PARENT_DIR = buildconfig.LEANHT_DIR
OUT_DIR1 = os.path.join(PARENT_DIR, 'iteration1')
OUT_DIR2 = os.path.join(PARENT_DIR, 'iteration2')
LEMMA_LENGTH = ThesaurusInstance._meta.get_field('lemma').max_length

ADJECTIVES = {'female', 'specific', 'small', 'again', 'young',
    'excessive', 'male',  'large',  'personified',  'little', 'renewed',
    'sudden', 'subordinate', 'temporary', 'official', 'inferior', 'minor',
    'short', 'chief', 'jewish',  'excessively', 'new', 'indian', 'black',
    'named', 'chinese', 'japanese', 'foreign', 'petty', 'subsidiary',
    'extreme', 'slight', 'formal', 'muslim', 'private', 'natural',
    'additional', 'second', 'old', 'professional', 'french', 'african',
    'secondary', 'portable', 'orthodox', 'complete', 'false', 'underground',
    'roman', 'rapid', 'scottish', 'partial', 'coarse', 'artificial',
    'first', 'repeated', 'hindu', 'round', 'subsequent', 'ornamental',
    'white', 'original', 'turkish', 'maori', 'buddhist', 'long', 'superior',
    'fresh', 'irish', 'green', 'special', 'proprietary', 'principal',
    'russian', 'particular', 'good', 'constant', 'red', 'ancient',
    'western', 'mutual', 'imitation', 'german',}


def make_lean_ht():
    # We do two iterations so that it's possible for two levels to be rolled
    #  up: a level may become a leaf node in iteration #1 (because
    #  its own leaf nodes get rolled up), and so becomes a candidate for
    #  rolling up in iteration #2.
    compile_iteration(IN_DIR, OUT_DIR1, sanitize=True, drop_instances=True)
    compile_iteration(OUT_DIR1, OUT_DIR2, deduplicate=True)


def compile_iteration(in_dir, out_dir, **kwargs):
    sanitize = kwargs.get('sanitize', False)
    drop_instances = kwargs.get('drop_instances', False)
    deduplicate = kwargs.get('deduplicate', False)

    iterator = ContentIterator(in_dir=in_dir, out_dir=out_dir, yield_mode='file')
    for classes in iterator.iterate():
        # Build a map of each class indexed by ID
        classmap = {thesclass.id(): thesclass for thesclass in classes}
        # Set of IDs marking classes which will be dropped
        dropped_classes = set()

        # Drop instances that are not usable
        if drop_instances:
            for thesclass in classes:
                if thesclass.instances():
                    wordclass = thesclass.wordclass(penn=True)
                    stripnodes = [instance for instance in
                                  thesclass.instances()
                                  if _is_not_usable(instance)]
                    if stripnodes:
                        for instance in stripnodes:
                            instance.selfdestruct()
                        # Reset the listed size of the class
                        new_size = thesclass.size() - len(stripnodes)
                        if thesclass.size() == thesclass.size(branch=True):
                            thesclass.reset_size(new_size, branch=True)
                        thesclass.reset_size(new_size)
                        if thesclass.size(branch=True) == 0:
                            dropped_classes.add(thesclass.id())

        # Roll up minor leaf nodes to the parent node
        for thesclass in [c for c in classes if not c.id() in dropped_classes]:
            thesclass.reload_instances()
            parentclass = classmap.get(thesclass.parent(), None)
            if parentclass:
                grandparentclass = classmap.get(parentclass.parent(), None)
            else:
                grandparentclass = None
            if _viable_for_rollup(thesclass, parentclass, grandparentclass):
                # Move instances from this class to the parent class
                for instance in thesclass.instances():
                    parentclass.node.append(instance.node)
                # Mark this class to be dropped
                dropped_classes.add(thesclass.id())

        # Remove child-node pointers for nodes which are about to be deleted
        for thesclass in [c for c in classes if not c.id() in dropped_classes]:
            for child_id in thesclass.child_nodes():
                if child_id in dropped_classes:
                    thesclass.remove_child(child_id)

        # Remove nodes for classes marked to be dropped
        for classid in dropped_classes:
            thesclass = classmap[classid]
            thesclass.selfdestruct()

        # Redo counts in the remaining classes
        for thesclass in [c for c in classes if not c.id() in dropped_classes]:
            thesclass.reload_instances()
            thesclass.reset_size(len(thesclass.instances()))
            if sanitize:
                for instance in thesclass.instances():
                    _sanitize_lemma(instance, thesclass.wordclass(penn=True))
            if deduplicate:
                _deduplicate_instances(thesclass)


def _is_not_usable(instance):
    if ' or ' in instance.lemma():
        return True
    elif '\u2014' in instance.lemma():
        return True
    elif ',' in instance.lemma():
        return True
    else:
        return False


def _viable_for_rollup(thesclass, parentclass, grandparentclass):
    if (thesclass.is_leaf_node() and
            thesclass.size() <= 10 and
            thesclass.level() >= 4 and
            parentclass and
            parentclass.wordclass()):
        if _label_viable_for_rollup(thesclass, parentclass, grandparentclass):
            return True
        elif _aligned_lemmas(thesclass, parentclass):
            return True
    return False


def _label_viable_for_rollup(thesclass, parentclass, grandparentclass):
    wordclass = thesclass.wordclass(penn=True)
    label = thesclass.label().lower().strip()
    parent_label = parentclass.label().lower()
    if not parent_label and grandparentclass:
        parent_label = grandparentclass.label().lower()
    if not parent_label:
        parent_label = 'qqzzqq' # Dummy to avoid erroneous matches against ''
    parent_labels = parent_label.split(' or ')
    parent_labels.append(parent_label)
    parent_labels = [p.strip() for p in parent_labels]

    if label in ('not', 'without') or label.startswith('not '):
        return False

    elif wordclass == 'NN':
        if (label.endswith(' of') and
                not re.search(r'(type|kind)s? of$', label)):
            response = False
        elif re.search(r' (in|for|with|who|which)$', label):
            response = False
        elif (any([label.endswith(p) for p in parent_labels]) and
                not ' of ' in label):
            response = True
        elif re.search(r'^(used|of|with|by|for|in|on|having) ', label):
            response = True
        elif re.search(r'(type|kind)s? of$', label):
            response = True
        elif re.search(r'^(specific|other)(| kinds| types)$', label):
            response = True
        elif re.search(r'^defined (by|in relation to) ', label):
            response = True
        elif re.search(r'^(others?|varieties|types)$', label):
            response = True
        elif (re.search(r'^[a-z]+(ing|ic|ical)$', label) and
                not label.startswith('being ')):
            # Adjectival qualifier
            response = True
        elif label in ADJECTIVES:
            # Adjectival qualifier
            response = True
        elif re.search(r'^[a-z]+ing ([a-z]+|[a-z]+ [a-z]+)$', label):
            # Adjectival phrase, like 'carrying belongings'
            response = True
        else:
            response = False

    elif wordclass == 'JJ':
        if (any([label.endswith(p) for p in parent_labels]) or
                label.startswith(parent_label + ' ')):
            response = True
        elif label in ('somewhat', 'rather', 'very',):
            response = True
        elif re.search(r'^[a-z-]+ly$', label):
            response = True
        else:
            response = False

    elif wordclass in ('RB', 'UH'):
        response = True

    elif wordclass == 'VB':
        if re.search(r'^(with|by|for|at|on|in|without|into) ', label):
            response = True
        elif re.search(r'^(of) ', label):
            response = True
        elif re.search(r'^[a-z-]+ly$', label):
            response = True
        elif any([label.startswith(p + ' ') for p in parent_labels]):
            response = True
        else:
            response = False

    else:
        response = False

    return response


def _aligned_lemmas(thesclass, parentclass):
    response = False
    if thesclass.wordclass(penn=True) in ('NN', 'JJ'):
        parent_lemmas = set()
        keywords = set()
        for instance in parentclass.instances():
            lemma = instance.lemma().replace('-', ' ').strip()
            words = lemma.split()
            if len(words) <= 2:
                keywords.add(words[-1])
            parent_lemmas.add(instance.lemma())
        for instance in [i for i in thesclass.instances()
                         if not i.lemma() in parent_lemmas]:
            lemma = instance.lemma().replace('-', ' ').strip()
            words = lemma.split()
            if len(words) == 2 and words[-1] in keywords:
                response = True

    #if response:
    #    print('---------------------------------------------------------')
    #    print(parentclass.breadcrumb())
    #    for i in parentclass.instances():
    #        print('\t', i.lemma())
    #    print(thesclass.breadcrumb())
    #    for i in thesclass.instances():
    #        print('\t', i.lemma())
    return response


def _sanitize_lemma(instance, wordclass):
    new_lemma = instance.lemma()
    new_lemma = re.sub(r'\([^()]+\)', '', new_lemma)
    new_lemma = re.sub(r'\([a-z]+$', '', new_lemma)
    new_lemma = re.sub(r'  +', ' ', new_lemma)
    new_lemma = new_lemma.strip()
    if wordclass == 'VB':
        new_lemma = re.sub(r'^to ', '', new_lemma)
    if wordclass == 'NN':
        new_lemma = re.sub(r'^(the|a|an) ', '', new_lemma)

    new_lemma = new_lemma[0:LEMMA_LENGTH]

    if new_lemma != instance.lemma():
        instance.node.find('./lemma').text = new_lemma
        instance.node.set('sortAlpha', lexical_sort(new_lemma))


def _deduplicate_instances(thesclass):
    thesclass.reload_instances()
    groups = defaultdict(list)
    for instance in thesclass.instances():
        groups[lexical_sort(instance.lemma())].append(instance)

    deletions = []
    for group in groups.values():
        if len(group) > 1:
            z = [i for i in group if not i.is_obsolete()] or group[:]
            z.sort(key=lambda i: i.num_quotations(), reverse=True)
            z.sort(key=lambda i: i.start_date())
            for instance in z[1:]:
                deletions.append(instance)

    if deletions:
        for instance in deletions:
            instance.selfdestruct()
        thesclass.reload_instances()
        thesclass.reset_size(len(thesclass.instances()))
