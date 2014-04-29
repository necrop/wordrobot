"""
light_pos_picker - out of two or more possible matches for the token,
picks the one whose part of speech seems to be the best match for the
context - or failing that, the one with the highest frequency.
"""

ARTICLES = {'the', 'a', 'an', 'his', 'her', 'my', 'their',
            'your', 'our', 'its', 'any'}
PRONOUNS = {'i', 'you', 'we', 'they'}
PRONOUNS3 = {'he', 'she', 'it'}
OBJECTS = {'me', 'him', 'her', 'it', 'us', 'them', 'himself',
           'herself', 'itself', 'myself', 'ourselves', 'themselves',
           'yourself', 'yourselves'}
AUXILIARIES = {'is', 'was', 'were', 'are', 'be', 'been'}
AUXILIARIES2 = {'have', 'has', 'had', 'having'}
PREPOSITIONS = {'in', 'on', 'with', 'at', 'through', 'into', 'onto',
                'upon', 'along', 'without', 'beside'}
ADJ_QUALIFIERS = {'very', 'really', 'quite', 'is', 'was', 'are', 'were', 'too'}
SENTENCE_ENDS = {'.', ':', ';', '!', '?'}
MODALS = {'can', 'will', 'shall', 'would', 'should', 'could', "'d",
          "'ll", 'not', "'n't"}


def light_pos_picker(token, candidates):
    wordclasses = set([c.wordclass for c in candidates])
    if token.previous_token():
        previous_token = token.previous_token().lower()
    else:
        previous_token = ''
    if token.next_token():
        next_token = token.next_token().lower()
    else:
        next_token = ''

    for c in candidates:
        c.score = 0
        if c.wordclass in ('NN', 'NNS', 'JJ'):
            if previous_token in ARTICLES or previous_token == 'of':
                c.score += 1

        if c.wordclass in ('NN', 'NNS', 'JJ'):
            if (next_token in ARTICLES or next_token in PRONOUNS or
                    next_token in PRONOUNS3 or next_token in OBJECTS):
                c.score -= 1

        if c.wordclass in ('NN', 'NNS'):
            if next_token in ('of', 'which'):
                c.score += 1

        if c.wordclass in ('NN',):
            if next_token in ('is', 'was', 'has', 'had', 'did', 'does'):
                c.score += 1

        if c.wordclass in ('NNS',):
            if next_token in ('are', 'were', 'have', 'had', 'did', 'do'):
                c.score += 1

        if c.wordclass in ('VB', 'VBZ', 'VBD', 'VBN', 'VBG', 'VBND'):
            if (next_token in ARTICLES or
                    next_token in AUXILIARIES or
                    next_token in OBJECTS or
                    next_token == "'s"):
                c.score += 1

        if c.wordclass in ('VB',):
            if previous_token in PRONOUNS:
                c.score += 1

        if c.wordclass in ('VBZ',):
            if previous_token in PRONOUNS3:
                c.score += 1

        if c.wordclass in ('VBD', 'VBND'):
            if previous_token in PRONOUNS or previous_token in PRONOUNS3:
                c.score += 1

        if c.wordclass in ('VBN', 'VBG', 'VBND'):
            if previous_token in AUXILIARIES:
                c.score += 1

        if c.wordclass in ('VBN', 'VBND'):
            if previous_token in AUXILIARIES2:
                c.score += 1
            if next_token == 'by':
                c.score += 0.5

        if c.wordclass in ('VB',):
            if previous_token == 'to' and next_token not in SENTENCE_ENDS:
                c.score += 0.5

        if c.wordclass in ('VB',):
            if previous_token in MODALS:
                c.score += 0.5

        if c.wordclass in ('VB', 'VBZ', 'VBD', 'VBN', 'VBND'):
            if previous_token in PREPOSITIONS:
                c.score -= 1

        if c.wordclass in ('VB', 'VBZ',):
            if previous_token in "'s":
                c.score -= 1

        if c.wordclass in ('IN',):
            if next_token in ARTICLES:
                c.score += 1

        if c.wordclass in ('JJ',):
            if next_token in PREPOSITIONS or next_token == "'s":
                c.score -= 1
            if (next_token == 'by' and
                    ('VBN' in wordclasses or 'VBND' in wordclasses)):
                c.score -= 1

            if previous_token in ADJ_QUALIFIERS:
                c.score += 1
            elif previous_token in ARTICLES and next_token in SENTENCE_ENDS:
                c.score -= 1

        if c.wordclass in ('VB', 'VBZ', 'VBD', 'VBN', 'VBND'):
            if next_token == '-':
                c.score -= 1

        if c.wordclass in ('JJ', 'RB'):
            if next_token in AUXILIARIES:
                c.score -= 0.5
            if next_token == '-':
                c.score += 0.5

    period = token.docperiod
    candidates.sort(key=lambda c: c.__dict__[period], reverse=True)
    candidates.sort(key=lambda c: c.score, reverse=True)
    #_display_results(previous_token, token.token, next_token, candidates)
    return candidates[0]


def _display_results(previous_token, token, next_token, candidates):
    """
    Used for debugging only
    """
    print('-----------------------------------------------------')
    print('%s -> %s -> %s' % (previous_token, token, next_token))
    for c in candidates:
        print('\t%s\t%s\t%f\t%d' % (c.wordform, c.wordclass, c.f2000, c.score))