
import re
from functools import lru_cache
from collections import namedtuple

from . import appsettings as local_settings
from ..models import Wordform, Lemma
from .lexicalsort import lexicalsort

CORE_WORDS = local_settings.CORE_WORDS
CALENDAR = local_settings.CALENDAR
INDEFINITE_ARTICLES = local_settings.INDEFINITE_ARTICLES
INFLECTIONS = local_settings.INFLECTIONS

ELIDED_V_PATTERN = re.compile(r"[OEoe]'er")
BarebonesResponse = namedtuple('BarebonesResponse',
                               ['wordform', 'wordclass', 'lemma'])


def lemma_lookup(token, sort, year, **kwargs):
    plural_check = kwargs.get('plural_check', True)
    strict = kwargs.get('strict', False)
    token_low = token.lower()

    target_lemma = INFLECTIONS.get(token_low, None)
    if (target_lemma is None and
            (token_low in CORE_WORDS or
            token_low in INDEFINITE_ARTICLES or
            token_low in CALENDAR)):
        target_lemma = token_low

    if target_lemma is not None:
        # For hardcoded core wordforms, we shortcut the process of
        #   the wordform and then getting the lemma; we just get the lemma
        #   directly/ This means we then have to fake a response with a skeleton
        #   wordform object containing the lemma.
        # Look up the lemma
        qset = _cached_lemma_lookup(target_lemma)
        # The one we want will be the most most frequent lemma
        lemma = qset.order_by('-frequency').first()
        # Fake a barebones Wordform object containing the lemma. We give the
        #  wordform the same wordclass as the lemma; which won't always be
        #  quote true, but should be close enough to be not worth
        #  worrying about.
        response = [BarebonesResponse(token, lemma.wordclass, lemma), ]
        return response

    else:
        antedating_margin = _set_antedating_margin(year)
        qset = _cached_wordform_lookup(sort)

        # If no results...
        if not qset.exists() and not strict:
            # If the token looks like it might be a plural
            #  (i.e. ends with 's'), try again with singular equivalent.
            if (plural_check and
                len(sort) >= 5 and
                sort.endswith('s') and
                not sort.endswith('ss')):
                sort_singular = sort.rstrip('s')
                qset = _cached_wordform_lookup(sort_singular)

            # Try converting -ise- forms to -ize-
            if not qset.exists() and 'is' in sort:
                match = re.search(r'(....is(e|ing|at|able))', sort)
                if match is not None:
                    before = match.group(1)
                    after = before.replace('s', 'z')
                    sort2 = sort.replace(before, after)
                    qset = _cached_wordform_lookup(sort2)
                    if qset.exists():
                        token = token.replace('is', 'iz')

            # Try modernizing archaic '-eth' and '-est' endings
            if (not qset.exists() and year < 1900 and
                    (sort.endswith('eth') or
                    sort.endswith('est'))):
                sort2 = re.sub(r"(...)e(th|st)$", r'\1s', sort)
                sort3 = re.sub(r"(...)e(th|st)$", r'\1es', sort)
                qset = _cached_wordform_lookup(sort2)
                if not qset.exists():
                    qset = _cached_wordform_lookup(sort3)
                qset = qset.filter(wordclass='VBZ')

            if (not qset.exists() and year < 1900 and
                    token.endswith("'st")):
                sort2 = re.sub(r"(...)st$", r'\1s', sort)
                sort3 = re.sub(r"(...)st$", r'\1es', sort)
                qset = _cached_wordform_lookup(sort2)
                if not qset.exists():
                    qset = _cached_wordform_lookup(sort3)
                qset = qset.filter(wordclass='VBZ')

            # Try modernizing archaic '-ick/-icke/-ique' to '-ic'
            if (not qset.exists() and year < 1800 and
                    re.search(r'i(ck|cke|que)$', sort)):
                sort2 = re.sub(r'i(ck|cke|que)$', r'ic', sort)
                qset = _cached_wordform_lookup(sort2)
                if qset.exists():
                    token = re.sub(r'i(ck|cke|que)$', r'ic', token)
                qset = qset.filter(wordclass='JJ')

            if not qset.exists() and year < 1800 and 'ickal' in sort:
                sort2 = sort.replace('ickal', 'ical')
                qset = _cached_wordform_lookup(sort2)
                if qset.exists():
                    token = token.replace('ickal', 'ical')
                qset = qset.filter(wordclass='JJ')

            # Try modernizing 'o'er' to 'over', etc.
            if (not qset.exists() and year < 1900 and
                    ELIDED_V_PATTERN.search(token)):
                sort2 = sort.replace('oer', 'over').replace('eer', 'ever')
                qset = _cached_wordform_lookup(sort2)
                if qset.exists():
                    token = token.replace("'er", 'ver')

            # Try modernizing 'flow'rets' to 'flowerets',
            #  'am'rous' to 'amorous',  etc.
            if not qset.exists() and "'" in token:
                token2 = token.replace("'", 'e')
                sort2 = lexicalsort(token2)
                qset = _cached_wordform_lookup(sort2)
                if qset.exists():
                    token = token2
                else:
                    token2 = token.replace("'", 'o')
                    sort2 = lexicalsort(token2)
                    qset = _cached_wordform_lookup(sort2)
                    if qset.exists():
                        token = token2

            # Try extending -in ending to -ing
            if not qset.exists() and year > 1850 and sort.endswith('in'):
                sort2 = sort + 'g'
                qset = _cached_wordform_lookup(sort2)
                if qset.exists():
                    token += 'g'

        if not qset.exists():
            response = []
        elif qset.count() == 1:
            qset = qset.filter(lemma__firstyear__lt=antedating_margin)
            response = list(qset)
        elif qset.count() > 1:
            qset2 = qset.filter(wordform=token)
            if qset2:
                qset = qset2
            qset = qset.filter(lemma__firstyear__lt=antedating_margin)
            response = list(qset)
        else:
            response = []

        return response


@lru_cache(maxsize=512)
def _cached_lemma_lookup(target):
    return Lemma.objects.filter(sort=target)


@lru_cache(maxsize=512)
def _cached_wordform_lookup(target):
    return Wordform.objects.filter(sort=target)


def _set_antedating_margin(year):
    """
    Set the margin by which antedating is plausible. If we find a lemma
    match for a given token, but the lemma's first date is more than
    x years after the document year, the match will be rejected.
    """
    if year > 1900:
        return year + 30
    elif year > 1800:
        return year + 50
    else:
        return year + 100
