
from . import appsettings as local_settings
from ..models import ProperName
from .lexicalsort import lexicalsort
from .utilities import json_safe, apostrophe_unmasker
from .lemmalookup import lemma_lookup
from .lightpospicker import light_pos_picker

CORE_WORDS = local_settings.CORE_WORDS
CALENDAR = local_settings.CALENDAR
INDEFINITE_ARTICLES = local_settings.INDEFINITE_ARTICLES
INFLECTIONS = local_settings.INFLECTIONS
WORDLIKE = local_settings.WORDLIKE
PROPER_NAME_BIGRAMS = local_settings.PROPER_NAME_BIGRAMS
PROPER_NAME_ENDS = local_settings.PROPER_NAME_ENDS
PROPER_NAME_TITLES = local_settings.PROPER_NAME_TITLES
CLOSING_PUNCTUATION = local_settings.CLOSING_PUNCTUATION
UNSPACED = set(('(', '[', '\u201c', '/', '-')) # no space before these


class Token(object):

    lemma_cache = {}

    def __init__(self, token, year):
        self.token_verbatim = _token_cleanup(token)
        self.token = _token_adjusted(self.token_verbatim, year)

        self.docyear = year  # Year of the document this comes from
        self.first = False  # Is this the first token in its sentence?
        self.last = False  # Is this the last token in its sentence?
        self.previous = None  # The preceding token
        self.next = None  # The following token
        self.proper_name = None  # Is this a proper name?
        self.newline = False  # Does this token start a new line?
        self.count = 0  # Occurrences of the token's lemma (gets set later)
        self.skip = False
        self.propername_test = None
        self.wordclass = None

    @classmethod
    def clear_cache(cls):
        cls.lemma_cache = {}

    def lower(self):
        return self.token.lower()

    def upper(self):
        return self.token.upper()

    def lexical_sort(self):
        return lexicalsort(self.token)

    def is_capitalized(self):
        """
        Return True if this token is capitalized (title-cased)
        """
        if len(self.token_verbatim) > 1 and self.token_verbatim.istitle():
            return True
        elif self.token_verbatim.startswith('Mc'):
            return True
        else:
            return False

    def follows_indefinite_article(self):
        """
        Return True if this token comes immediately after an
        indefinite article.
        """
        if (self.previous is not None and
            self.previous.lower() in INDEFINITE_ARTICLES):
            return True
        else:
            return False

    def is_wordlike(self):
        """
        Return True if this looks roughly like a word.

        This determines whether the token will be investigated
        further (looked up n the database, etc.)
        """
        try:
            return self._is_wordlike
        except AttributeError:
            if self.token.isalpha():
                self._is_wordlike = True
            elif (len(self.token) > 2 and
                  all([segment.isalpha() for segment in self.token.split('-')])):
                self._is_wordlike = True
            elif (len(self.token) > 2 and
                  all([segment.isalpha() for segment in
                       self.token.strip("'").split("'")])):
                self._is_wordlike = True
            elif self.token in WORDLIKE:
                self._is_wordlike = True
            else:
                self._is_wordlike = False
            return self._is_wordlike

    def is_core(self):
        if self.lower() in CORE_WORDS:
            return True
        else:
            return False

    def starts_sentence(self):
        if self.first:
            return True
        elif (self.previous and
                  self.previous.first and
                  not self.previous.is_wordlike()):
            return True
        else:
            return False

    def next_token(self):
        try:
            return self.next.token
        except AttributeError:
            return None

    def previous_token(self):
        try:
            return self.previous.token
        except AttributeError:
            return None

    def next_token_verbatim(self):
        try:
            return self.next.token_verbatim
        except AttributeError:
            return None

    def previous_token_verbatim(self):
        try:
            return self.previous.token_verbatim
        except AttributeError:
            return None

    def check_proper_name(self, method=None):
        if self.proper_name is not None:
            return
        elif not self.is_wordlike() or not self.is_capitalized():
            self.proper_name = False

        elif not method or method == 'capitalization':
            if self._is_proper_bigram():
                self.proper_name = True
                self.next.proper_name = True
            elif self.is_core():
                self.proper_name = False
            elif self.lower() in INFLECTIONS:
                self.proper_name = False
            elif self.lower() in CALENDAR:
                self.proper_name = False
            elif self.token == 'I':
                self.proper_name = False
            elif self.follows_indefinite_article():
                self.proper_name = False
            elif not self.lemma_manager():
                self.proper_name = True

        elif (method == 'neighbours' and
                self.is_capitalized() and
                not self.starts_sentence()):
            if (self.previous and
                    self.previous.is_capitalized() and
                    not self.previous.starts_sentence() and
                    self.previous.proper_name is not False):
                self.proper_name = True
                self.previous.proper_name = True
            elif (self.next and
                    self.next.is_capitalized() and
                    self.next.proper_name is not False):
                self.proper_name = True
                self.next.proper_name = True

        elif method == 'unambiguous':
            qset = ProperName.objects.filter(sort=self.lexical_sort(),
                                             lemma=self.token_verbatim)
            if qset.exists() and qset.first().common:
                self.proper_name = True
            elif not qset.exists():
                self.proper_name = False
            else:
                self.propername_test = qset.first().lemma

        elif method == 'midsentence' and not self.starts_sentence():
            if self.lemma_manager() and self.lemma_manager().lemma.istitle():
                self.proper_name = False
            elif self.propername_test:
                self.proper_name = True

        elif method == 'firstword' and self.starts_sentence():
            if self.lemma_manager():
                self.proper_name = False
            else:
                self.proper_name = True

    def repair_tokenization_errors(self):
        """
        In case of overzealous tokenization, e.g where 'wanna' has been
        split to 'wan' + 'na', we repair it and skip the next token  
        """
        if self.next_token() == 'na' and self.lower() in ('wan', 'gon'):
            self.token += 'na'
            self.token_verbatim += 'na'
            self.omit_next()

    def omit_previous(self):
        """
        Mark the previous token for disposal; and move the 'previous'
        pointer back to the preceding token (in any).
        """
        if self.previous:
            self.previous.skip = True

    def omit_next(self):
        """
        Mark the next token for disposal; and move the 'next'
        pointer forward to the following token (in any).
        """
        if self.next:
            self.next.skip = True

    def _is_proper_bigram(self):
        if (self.next_token() in PROPER_NAME_ENDS and
                self.is_capitalized()):
            return True
        elif (self.token in PROPER_NAME_TITLES and
                self.next and
                self.next.is_capitalized()):
            return True
        elif (self.token in PROPER_NAME_BIGRAMS and
                self.next_token() in PROPER_NAME_BIGRAMS[self.token]):
            return True
        else:
            return False

    def lemma(self):
        if self.lemma_manager() is None:
            return None
        else:
            return self.lemma_manager().lemma

    def lemma_manager(self):
        try:
            return self._lemma_manager
        except AttributeError:
            self.find_lemma()
            return self._lemma_manager

    def reset_lemma(self, new_lemma_manager):
        self._lemma_manager = new_lemma_manager

    def nix_lemma(self):
        self._lemma_manager = None

    def is_in_oed(self):
        if self.lemma_manager() is None:
            return False
        else:
            return True

    def is_missing_from_oed(self):
        if (self.is_wordlike() and
            not self.proper_name and
            not self.is_in_oed()):
            return True
        else:
            return False

    def find_lemma(self):
        if self.is_wordlike():
            try:
                Token.lemma_cache[self.lower()]
            except KeyError:
                Token.lemma_cache[self.lower()] = lemma_lookup(self.token,
                                                               self.lexical_sort(),
                                                               self.docyear)
            candidates = Token.lemma_cache[self.lower()]
            if len(candidates) == 1:
                self._lemma_manager = candidates[0].lemma
                self.token = candidates[0].wordform
                self.wordclass = candidates[0].wordclass
            elif len(candidates) > 1:
                winner = light_pos_picker(self, candidates)
                self._lemma_manager = winner.lemma
                self.token = winner.wordform
                self.wordclass = winner.wordclass
            else:
                self._lemma_manager = None
        else:
            self._lemma_manager = None

    def space_before(self):
        if (self.token in CLOSING_PUNCTUATION or
                self.token.startswith("'") or
                self.token == "n't" or
                self.token == '-'):
            return False
        elif self.previous_token() in UNSPACED:
            return False
        else:
            return True

    def status(self):
        if self.is_in_oed():
            _status = 'oed'
        elif self.proper_name:
            _status = 'proper'
        elif self.is_wordlike():
            _status = 'missing'
        else:
            _status = 'punc'
        return _status

    def to_list(self):
        if self.newline:
            space_before = 2
        elif self.space_before():
            space_before = 1
        else:
            space_before = 0
        return [json_safe(self.token_verbatim),
                self.status(),
                space_before,]

    #=============================================================
    # The following functions are not strictly needed by the
    #  application itself, but may be useful for testing.
    # Essentially, these are all just wrappers for calls to the
    #  token's linked Lemma object (if any).
    #=============================================================

    def _languages(self):
        if self.lemma_manager() is None:
            return None, None
        else:
            language_name = self.lemma_manager().language_name()
            family = self.lemma_manager().language_family()
            return language_name, family

    def language(self):
        if self._languages()[0]:
            return self._languages()[0]
        else:
            return 'not specified'

    def language_family(self):
        if self._languages()[1]:
            return self._languages()[1]
        else:
            return 'other'

    def url(self):
        if self.lemma_manager() is None:
            return None
        else:
            return self.lemma_manager().url()

    def oed_identifier(self):
        if self.lemma_manager() is None:
            return None
        else:
            return self.lemma_manager().oed_identifier()

    def frequency(self):
        if self.lemma_manager() is None:
            return None
        else:
            if self.lemma_manager().frequency > 1:
                return int(self.lemma_manager().frequency)
            else:
                return self.lemma_manager().frequency

    def log_band(self):
        if self.lemma_manager() is None:
            return None
        else:
            return self.lemma_manager().log_band()


def _token_cleanup(text):
    """
    Clean up the form of the token as it's initially passed in
    """
    # Unmask apostrophes (previously masked in tokenizer() to
    #  prevent erroneous splitting).
    text = apostrophe_unmasker(text)
    # Convert double-quotes to a single character
    if text == "``":
        text = '\u201c'
    elif text == "''":
        text = '\u201d'
    return text


def _token_adjusted(text, year):
    if year > 1950 and text.endswith("in'"):
        return text.rstrip("'") + 'g'
    else:
        return text
