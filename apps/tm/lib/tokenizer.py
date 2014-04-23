
import re

from nltk.tokenize import word_tokenize, sent_tokenize
from .token import Token
from .lemmacollection import LemmaCollection
from .opencompounds import (check_for_open_bigram,
                            check_for_open_trigram,
                            check_for_hyphen_trigram,
                            check_for_hyphen_5gram)
from .utilities import apostrophe_masker, stop_masker, stop_unmasker


# We need to space these out, because the tokenizer does not do so
SPACERS = ('\u2013', '\u2014', '\u201c', '\u201d', '\u2018', '/')
ADJACENT_APOSTROPHE = re.compile(r"(^'| '|\(')([a-zA-Z])")


def tokenizer(text, year):

    #-----------------------------------------------
    # Clean-up and lineation
    #-----------------------------------------------

    for char in SPACERS:
        text = text.replace(char, ' %s ' % char)
    text = text.replace('\u2019', "'")
    text = ADJACENT_APOSTROPHE.sub(r"\1 \2", text)

    # Turn hyphens used as dashes into en-dashes (so not confused
    #  with genuine hyphens)
    text = text.replace(' - ', ' \u2013 ').replace(',- ', ',\u2013 ')
    # Space out hyphens, so that hyphenated words get tokenized
    #  separately (at first, at least)
    text = text.replace('-', ' - ')

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    lines = [apostrophe_masker(l, year) for l in lines]
    lines = [stop_masker(l) for l in lines]

    #-----------------------------------------------
    # Tokenization and lemmatization
    #-----------------------------------------------
    tokens = []
    for line in lines:
        sentences = sent_tokenize(line)
        line_tokens = []
        for sentence in sentences:
            sentence = stop_unmasker(sentence)
            # Tokenize this sentence
            sentence = re.sub(r'([:,])$', r' \1', sentence)
            sentence_tokens = [Token(w, year, sentence) for w in
                               word_tokenize(sentence)]
            # Identify lemmas for each token (where possible)
            sentence_tokens = _identify_lemmas(sentence_tokens)

            # Add tokens from this sentence to line_tokens
            line_tokens.extend(sentence_tokens)
        if line_tokens:
            line_tokens[0].newline = True
        tokens.extend(line_tokens)

    #-----------------------------------------------
    # Figure out which tokens are proper names
    #
    # (We do this *after* concatenating all the tokens together,
    #  rather than doing it sentence by sentence,
    #  so that we can take advantage of information across the
    #  whole text. For example, an unambiguous proper name in one position
    #  can help to disambiguate the same name in another position.)
    #-----------------------------------------------
    tokens = _find_proper_names(tokens)

    #-----------------------------------------------
    # Collate lemmas
    #-----------------------------------------------
    lemma_collection = LemmaCollection(tokens)
    lemma_collection.add_counts_to_tokens(tokens)

    return tokens, lemma_collection


def _identify_lemmas(tokens):
    tokens = _mark_token_positions(tokens)

    #-----------------------------------------------
    # Repair overzealous tokenization;
    #  e.g. 'wan', 'na' gets fixed to 'wanna'
    #-----------------------------------------------

    for token in tokens:
        token.repair_tokenization_errors()
    tokens = _drop_discarded_tokens(tokens)

    #-----------------------------------------------
    # Find lemmas
    #-----------------------------------------------

    for token in tokens:
        token.find_lemma()

    #-----------------------------------------------
    # Find hyphenated + open compounds
    #-----------------------------------------------

    for token in tokens:
        check_for_hyphen_5gram(token)
        check_for_hyphen_trigram(token)
    tokens = _drop_discarded_tokens(tokens)

    for token in tokens:
        check_for_open_trigram(token)
        check_for_open_bigram(token)
    tokens = _drop_discarded_tokens(tokens)

    #------------------------------------------------
    # Outstanding pos-checking for compounds
    #  (This had to wait till we'd done housekeeping on previous/next tokens)
    #------------------------------------------------
    for token in tokens:
        try:
            token.compound_candidates
        except AttributeError:
            pass
        else:
            winner = token.pick_candidate_by_pos(token.compound_candidates)
            token.reset_lemma(winner.lemma)

    return tokens


def _drop_discarded_tokens(tokens):
    tokens = [t for t in tokens if not t.skip]
    tokens = _mark_token_positions(tokens)
    return tokens


def _mark_token_positions(tokens):
    # Mark the first and last tokens in the sentence
    if tokens:
        tokens[0].first = True
        tokens[-1].last = True
    # Make each token aware of its previous and following
    #  neighbours
    for i, token in enumerate(tokens):
        try:
            token.previous = tokens[i - 1]
        except IndexError:
            token.previous = None
        try:
            token.next = tokens[i + 1]
        except IndexError:
            token.next = None
    return tokens


def _find_proper_names(tokens):
    for token in tokens:
        token.check_proper_name(method='capitalization')

    # Tag words which match other words that have already been tagged
    common = set([t.lower() for t in tokens if t.proper_name is False])
    for token in [t for t in tokens if t.proper_name is None
                  and t.lower() in common]:
        token.proper_name = False
    # Tag names which match other names that have already been tagged
    proper = set([t.token_verbatim for t in tokens if t.proper_name is True])
    for token in [t for t in tokens if t.proper_name is None
                  and t.token_verbatim in proper]:
        token.proper_name = True

    for token in tokens:
        token.check_proper_name(method='neighbours')
    for token in tokens:
        token.check_proper_name(method='unambiguous')
        token.check_proper_name(method='midsentence')

    # Tag names which match other names that have already been tagged
    proper = set([t.token_verbatim for t in tokens if t.proper_name is True])
    for token in [t for t in tokens if t.proper_name is None
                  and t.token_verbatim in proper]:
        token.proper_name = True

    for token in tokens:
        token.check_proper_name(method='firstword')

    # Remove any lemma reference from tokens which have been identified as
    #  proper names
    for token in [t for t in tokens if t.proper_name is True]:
        token.nix_lemma()
        token.token = token.token_verbatim
    return tokens
