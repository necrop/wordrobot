import json
import sys

from django.db import models

OED_BASE_URL = 'http://www.oed.com/'


class ThesaurusClass(models.Model):

    label = models.CharField(max_length=200, null=True)
    wordclass = models.CharField(max_length=20, null=True)
    level = models.IntegerField()
    parent = models.ForeignKey('self', null=True)
    node_size = models.IntegerField()
    branch_size = models.IntegerField()

    class Meta:
        app_label = 'tm'

    def ancestors(self):
        """
        Returns a list of ancestor classes in ascending order,
        beginning with self.

        Note that that the present class is included as the first element
        of the list
        """
        ancestor_list = [self,]
        if self.parent is not None:
            ancestor_list.extend(self.parent.ancestors())
        return ancestor_list

    def ancestor(self, level=1):
        """
        Returns the ancestor class at a specified level (defaults to 1)
        """
        if self.level == level:
            return self
        for a in self.ancestors():
            if a.level == level:
                return a
        return None

    def breadcrumb(self):
        ancestors = reversed(self.ancestors())
        ancestor_strings = []
        found_wordclass = False
        for a in ancestors:
            label = a.label or ''
            if a.wordclass is not None and not found_wordclass:
                ancestor_strings.append('%s [%s]' % (label, a.wordclass))
                found_wordclass = True
            else:
                ancestor_strings.append(label)
        return ' \u00bb '.join([a.strip() for a in ancestor_strings[1:] ])

    def indented(self):
        def recurse(node, val):
            if node.superordinate is not None:
                val += '\u00a0\u00a0\u00a0\u00a0'
                return recurse(node.superordinate, val)
            else:
                return val
        return recurse(self, '') + self.breadcrumb()

    def oed_url(self):
        template = '%sview/th/class/%d'
        return template % (OED_BASE_URL, self.id)

    def instances(self):
        return self.thesaurusinstance_set.all()

    def json_instances(self):
        return json.dumps([instance.to_dict() for instance
                           in self.instances()])

    def to_dict(self):
        instances = [i.to_dict() for i in self.instances()]
        return {'id': self.id,
                'breadcrumb': self.breadcrumb(),
                'instances': instances}

    def to_json(self):
        return json.dumps(self.to_dict())


class ThesaurusInstance(models.Model):

    lemma = models.CharField(max_length=100, db_index=True)
    refentry = models.IntegerField(db_index=True)
    refid = models.IntegerField(db_index=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    inflections = models.CharField(max_length=100, null=True)
    thesclass = models.ForeignKey('ThesaurusClass')

    class Meta:
        app_label = 'tm'
        ordering = ['start_year']

    def breadcrumb(self):
        if self.thesclass is None:
            return ''
        else:
            return self.thesclass.breadcrumb()

    def wordclass(self):
        if self.thesclass is None:
            return None
        else:
            return self.thesclass.wordclass

    def oed_url(self):
        template = '%sview/Entry/%d#eid%d'
        return template % (OED_BASE_URL, self.refentry, self.refid)

    def to_dict(self):
        response = {field: self.__dict__[field]
                    for field in ('lemma', 'refentry', 'refid',
                                  'start_year', 'end_year',)}
        response['infstring'] = self.inflections
        return response
