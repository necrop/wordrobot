"""
compounds - functions for testing for open and hyphenated
bigrams, trigrams, and 5-grams.
"""

from . import appsettings as local_settings
from .lexicalsort import lexicalsort
from .lemmalookup import lemma_lookup

CORE_WORDS = local_settings.CORE_WORDS
CORE_VERBS = local_settings.CORE_VERBS
MIDDLE_WORDS_FOREIGN = {'de', 'la', 'du', 'en', 'à', 'au'}
MIDDLE_WORDS = {'of', 'and', 'in'} | MIDDLE_WORDS_FOREIGN


def check_for_open_bigram(token):
    if not _plausible_bigram(token):
        return False

    hypothesis = token.token + ' ' + token.next_token()
    compound_lemma = _compound_lookup(hypothesis, token.docyear, strict=True)
    if not compound_lemma:
        return False

    # We require an exact match in order for this hypothesis
    #  to be allowed; unless this is the first word of the
    #  sentence, in which case we allow capitalization.
    # We also allow for regular pluralization.
    allowed = False
    if compound_lemma.wordclass not in ('NN', 'NNS', 'NP', 'JJ', 'RB'):
        pass
    elif (compound_lemma.lemma == hypothesis or
            compound_lemma.lemma + 's' == hypothesis or
            compound_lemma.lemma + 'es' == hypothesis):
        allowed = True
    elif (token.starts_sentence() and
            compound_lemma.lemma.capitalize() == hypothesis):
        allowed = True
    elif (token.previous and
            compound_lemma.wordclass in ('NN', 'NNS') and
            token.previous.lower() in ('a', 'an', 'the')):
        allowed = True

    if allowed:
        token.token = hypothesis
        token.token_verbatim += ' ' + token.next.token_verbatim
        token.reset_lemma(compound_lemma)
        token.omit_next()
        return True
    else:
        return False


def check_for_open_trigram(token):
    if not _plausible_open_trigram(token):
        return False

    hypothesis = (token.previous_token() + ' ' + token.token + ' '
                  + token.next_token())
    compound_lemma = _compound_lookup(hypothesis, token.docyear, strict=True)
    if not compound_lemma:
        return False

    token.token = hypothesis
    token.token_verbatim = (token.previous.token_verbatim + ' ' +
                            token.token_verbatim + ' ' +
                            token.next.token_verbatim)
    token.reset_lemma(compound_lemma)
    token.omit_previous()
    token.omit_next()
    return True


def check_for_hyphen_trigram(token):
    if not _plausible_hyphen_trigram(token):
        return False

    hypothesis = (token.previous_token() + '-' + token.next_token())
    compound_lemma = _compound_lookup(hypothesis, token.docyear, strict=False)
    if not compound_lemma:
        return False

    token.token = hypothesis
    token.token_verbatim = (token.previous.token_verbatim + '-' +
                            token.next.token_verbatim)
    token.reset_lemma(compound_lemma)
    token.omit_previous()
    token.omit_next()
    return True


def check_for_hyphen_5gram(token):
    if not _plausible_hyphen_5gram(token):
        return False

    hypothesis = (token.previous.previous_token() + '-' + token.token +
                  '-' + token.next.next_token())
    compound_lemma = _compound_lookup(hypothesis, token.docyear, strict=False)
    if not compound_lemma:
        return False

    token.token = hypothesis
    token.token_verbatim = (token.previous.previous.token_verbatim + '-' +
                            token.token_verbatim + '-' +
                            token.next.next.token_verbatim)
    token.reset_lemma(compound_lemma)
    token.previous.omit_previous()
    token.next.omit_next()
    token.omit_previous()
    token.omit_next()
    return True


def _plausible_bigram(token):
    """
    Return True if this token plus the next token could plausibly
    form an open bigram; return False otherwise.
    """
    if (token.last or
            token.is_core() or
            token.next.is_core() or
            token.skip or
            token.next.skip or
            token.lemma() in CORE_VERBS or
            token.next.lemma() in CORE_VERBS or
            len(token.next.token) < 3 or
            not token.is_wordlike() or
            not token.next.is_wordlike() or
            token.token.endswith('ly') or  # don't bother with adverbs
            token.next.token.endswith('ly')):
            #'-' in token.token or
            #'-' in token.next.token):
        return False
    if len(token.token) < 3 and token.lower() not in ('de', 'en'):
        return False

    return True


def _plausible_open_trigram(token):
    """
    Return True if this token plus the previous and next tokens could
    plausibly form an open trigram; return False otherwise.
    """
    if not token.token in MIDDLE_WORDS:
        return False
    if (not token.previous or
            not token.next or
            token.skip or
            token.previous.skip or
            token.next.skip):
        return False
    if (not token.previous.is_wordlike() or
            not token.next.is_wordlike() or
            token.previous.lower() in CORE_WORDS or
            token.next.lower() in CORE_WORDS or
            token.previous.lower() in CORE_VERBS or
            token.next.lower() in CORE_VERBS):
        return False

    if (len(token.previous.token) < 3 or
            len(token.next.token) < 3 or
            token.previous.token.endswith('ly') or  # don't bother with adverbs
            token.next.token.endswith('ly')):
        return False

    # The preceding and following words have to be recognized English
    #  words; unless the middle word is foreign, in which case we can be
    #  more flexible
    if (token.token in MIDDLE_WORDS_FOREIGN or
            (token.previous.is_in_oed() and token.next.is_in_oed())):
        return True
    else:
        return False


def _plausible_hyphen_trigram(token):
    """
    Return True if this is a hyphen, and the previous and next tokens could
    plausibly form a hyphenated trigram, e.g. |easy|-|chair|;
    return False otherwise.
    """
    if token.token != '-':
        return False
    if (not token.previous or
            not token.next or
            token.skip or
            token.previous.skip or
            token.next.skip):
        return False
    if (not token.previous.is_wordlike() or
            not token.next.is_wordlike()):
        return False
    if token.next.next_token() == '-':
        return False
    return True



def _plausible_hyphen_5gram(token):
    """
    Return True if the previous and following tokens could plausibly
    form a hyphenated 5-gram, e.g. |salt|-|and|-|pepper|
    (where 'and' represents the current position);
    return False otherwise.
    """
    if token.previous_token() != '-' or token.next_token() != '-':
        return False
    if (not token.is_wordlike() or
            not token.previous.previous or
            not token.previous.previous.is_wordlike() or
            not token.next.next or
            not token.next.next.is_wordlike()):
        return False
    return True


def _compound_lookup(hypothesis, year, strict=True):
    candidates = lemma_lookup(hypothesis,
                              lexicalsort(hypothesis),
                              year,
                              strict=strict)
    if not candidates:
        return None
    else:
        return candidates[0].lemma
