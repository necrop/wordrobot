
import re
import json

from django.utils.text import normalize_newlines

from .tokenizer import tokenizer
from .token import Token


class TextManager(object):

    def __init__(self, text, year):
        Token.clear_cache()
        self.text = normalize_newlines(text)
        self.tokens, self.lemmas = tokenizer(self.text, year)

    def teaser(self, length=50):
        clean = self.text.replace('\t', ' ').replace('\n', ' ').strip()
        clean = re.sub(r'  +', ' ', clean)
        clean = clean[:length]
        words = clean.split(' ')
        if len(words) > 3:
            # Remove the last word, since this may be incomplete
            words.pop()
        return ' '.join(words)

    def lemmas_datastruct(self, **kwargs):
        try:
            self._lemmas_datastruct
        except AttributeError:
            self._lemmas_datastruct = self.lemmas.datastruct()
        if kwargs.get('formalism') == 'json':
            return json.dumps(self._lemmas_datastruct)
        else:
            return self._lemmas_datastruct

    def tokens_datastruct(self, **kwargs):
        try:
            self._tokens_datastruct
        except AttributeError:
            # Note the index position of each lemma in
            #  lemmas_datastruct; we'll use index positions
            #  as pointers from tokens to their lemmas
            lemma_index = {lemma[0]: i for i, lemma in
                           enumerate(self.lemmas_datastruct())}

            self._tokens_datastruct = []
            for token in self.tokens:
                data = token.to_list()
                if token.is_in_oed():
                    # Include the index position of its lemma,
                    #  and the wordclass
                    lemma_id = token.lemma_manager().id
                    data.append(lemma_index[lemma_id])
                    data.append(token.wordclass)
                self._tokens_datastruct.append(data)
        if kwargs.get('formalism') == 'json':
            return json.dumps(self._tokens_datastruct)
        else:
            return self._tokens_datastruct

    def num_tokens(self):
        return len(self.tokens)

    def num_words(self):
        try:
            return self._num_words
        except AttributeError:
            self._num_words = len([t for t in self.tokens if t.is_wordlike()])
            return self._num_words

    def language_ratio(self, family):
        """
        Return the ratio of words from given language family
        (Germanic or Romance)
        """
        if family.lower() == 'romance':
            langs = set(('Latin', 'Romance'))
        elif family.lower() == 'germanic':
            langs = set(('Germanic',))
        else:
            langs = set()
        count = sum([lemma.token_count() for lemma in self.lemmas.lemmas()
                     if lemma.language_family() in langs])
        return count / self.num_words()

    def average_word_length(self):
        """
        Return the mean average word length
        """
        total = sum([len(token.token) for token in self.tokens
                     if token.is_wordlike()])
        return total / self.num_words()

    def cumulative_ratio(self, year):
        """
        Return the ratio of words that existed at a given date
        """
        count = sum([lemma.token_count() for lemma in self.lemmas.lemmas()
                     if lemma.firstyear <= year])
        return count / self.num_words()

    def profile_stats(self):
        try:
            return self._profile_stats
        except AttributeError:
            self._profile_stats = {
                'germanic': self.language_ratio('Germanic'),
                'romance': self.language_ratio('Romance'),
                'wordlength': self.average_word_length(),
                'r1200': self.cumulative_ratio(1200),
                'r1500': self.cumulative_ratio(1500),
            }
            return self._profile_stats

    #=============================================================
    # The following functions are not strictly needed by the
    #  application itself, but may be useful for testing.
    #=============================================================

    def num_recognized_tokens(self):
        return len([t for t in self.tokens if t.is_in_oed()])

    def num_lemmas(self):
        return len(self.lemmas)
