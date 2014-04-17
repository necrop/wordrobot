from django.db import models
from django.core.urlresolvers import reverse

from .lib import appsettings
from .lib.utilities import json_safe

# We import these so that they get picked up by syncdb
from .htmodels import ThesaurusClass, ThesaurusInstance

OED_BASE_URL = 'http://www.oed.com/'
URL_TEMPLATE = OED_BASE_URL + 'view/Entry/%s'
LANGUAGE_ABBREVIATIONS = appsettings.LANGUAGE_ABBREVIATIONS
THESAURUS_BARRED = appsettings.THESAURUS_BARRED


class Language(models.Model):

    name = models.CharField(max_length=40, db_index=True)
    family = models.ForeignKey('self', null=True)


class Definition(models.Model):

    text = models.CharField(max_length=100)


class Lemma(models.Model):

    lemma = models.CharField(max_length=40)
    sort = models.CharField(max_length=40, db_index=True)
    wordclass = models.CharField(max_length=10, null=True)
    frequency = models.FloatField(null=True)
    firstyear = models.IntegerField(null=True)
    lastyear = models.IntegerField(null=True)
    refentry = models.IntegerField()
    refid = models.IntegerField(null=True)
    language = models.ForeignKey('Language', null=True)
    definition = models.ForeignKey('Definition', null=True)
    thesaurus = models.ForeignKey('ThesaurusClass', null=True)

    class Meta:
        ordering = ['sort', ]

    def __unicode__(self):
        if self.refid:
            return '%s (%d#eid%d)' % (self.lemma, self.refentry, self.refid)
        else:
            return '%s (%d)' % (self.lemma, self.refentry)

    def oed_identifier(self):
        if self.refid:
            return '%d#eid%d' % (self.refentry, self.refid)
        else:
            return '%d' % self.refentry

    def url(self):
        return URL_TEMPLATE % self.oed_identifier()

    def language_name(self):
        if self.language is None:
            return None
        else:
            return self.language.name

    def language_family(self):
        if self.language is None or self.language.family is None:
            return None
        else:
            return self.language.family.name

    def token_count(self):
        try:
            return self.count
        except AttributeError:
            return 1

    def has_definition(self):
        """
        Return 1 or 0, depending on whether the lemma does or does
        not have a definition stored in the database 
        """
        if self.definition:
            return 1
        else:
            return 0

    def to_list(self):
        def abbreviate_language(language):
            if language in LANGUAGE_ABBREVIATIONS:
                return LANGUAGE_ABBREVIATIONS[language]
            else:
                return language

        def abbreviate_sortcode(lemma, sort):
            if sort == lemma:
                return ''
            else:
                return sort

        def theslink(lemma, thesaurus_id):
            if lemma in THESAURUS_BARRED:
                thesaurus_id = None
            return int(thesaurus_id or 0)

        # We don't include the definition (if any), so as to avoid
        #  bloating the JSON packet unnecessarily. (Most of the time
        #  the definition won't be invoked).
        # But we include the ID of the definition in the Definition
        #  table (if any), and the ID of the thesaurus class in the
        #  ThesaurusClass table (if any), so that it will be possible
        #  to fetch these via AJAX if required.
        return [self.id,
                self.oed_identifier(),
                json_safe(self.lemma),
                abbreviate_sortcode(self.lemma, self.sort),
                self.frequency,
                self.firstyear,
                abbreviate_language(self.language_name() or 'undefined'),
                abbreviate_language(self.language_family() or 'undefined'),
                self.token_count(),
                int(self.definition_id or 0),
                theslink(self.lemma, self.thesaurus_id), ]


class Wordform(models.Model):

    wordform = models.CharField(max_length=40)
    sort = models.CharField(max_length=40, db_index=True)
    wordclass = models.CharField(max_length=10, null=True)
    frequency = models.FloatField(null=True)
    lemma = models.ForeignKey('Lemma')

    class Meta:
        ordering = ['-frequency', ]

    def __repr__(self):
        if self.frequency:
            return '<Wordform: %s/%s (f=%f)>' % (self.wordform,
                                                 self.wordclass,
                                                 self.frequency)
        else:
            return '<Wordform: %s/%s>' % (self.wordform, self.wordclass)


class ProperName(models.Model):

    lemma = models.CharField(max_length=40)
    sort = models.CharField(max_length=40, db_index=True)
    common = models.BooleanField()


class Document(models.Model):

    author = models.CharField(max_length=40)
    authorsort = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=50)
    titlesort = models.CharField(max_length=50, db_index=True)
    year = models.IntegerField()
    text = models.TextField()
    lemmas = models.TextField()
    tokens = models.TextField()
    teaser = models.CharField(max_length=50)
    randomsort = models.IntegerField(db_index=True)

    class Meta:
        ordering = ['authorsort', 'titlesort', ]

    def get_absolute_url(self):
        return reverse('tm:display_canned',
                       kwargs={'author': self.authorsort,
                               'title': self.titlesort})

    def to_list(self):
        return [self.get_absolute_url(),
                json_safe(self.author),
                self.authorsort,
                json_safe(self.title),
                self.titlesort,
                self.year,
                json_safe(self.teaser), ]


class UserSubmission(models.Model):

    identifier = models.CharField(max_length=6, db_index=True)
    author = models.CharField(max_length=40, null=True)
    title = models.CharField(max_length=50)
    year = models.IntegerField()
    text = models.TextField()
    datestamp = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse('tm:display_stored',
                       kwargs={'identifier': self.identifier,})
