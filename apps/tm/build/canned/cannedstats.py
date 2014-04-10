from collections import defaultdict

from django.core.management.base import BaseCommand
import numpy

from apps.tm.build.canned.cannedloader import CannedLoader
from apps.tm.lib.textmanager import TextManager


class Command(BaseCommand):
    help = 'Key statistics for canned documents'

    def handle(self, *args, **options):
        std_arrays = defaultdict(list)
        doclist = []
        canned_loader = CannedLoader()
        for doc in canned_loader.iterate():
            # Process this document
            tm = TextManager(doc.text, doc.year)
            # Trace progress message
            self.stdout.write(doc.title + ' ' + doc.author)
            for key, value in sorted(tm.profile_stats().items()):
                std_arrays[key].append(value)
            doclist.append((doc.author + ', ' + doc.title, tm.profile_stats()))

        mean_averages = {key: numpy.mean(values)
                         for key, values in std_arrays.items()}
        standard_deviations = {key: numpy.std(values)
                               for key, values in std_arrays.items()}
        doclist = [(title, _convert_to_zscores(stats, mean_averages,
                   standard_deviations)) for title, stats in doclist]

        for i, doc in enumerate(doclist):
            title, stats = doc
            rankings = []
            for j, doc2 in enumerate(doclist):
                if j == i:
                    continue
                distance = _measure_distance(doc, doc2)
                rankings.append((doc2[0], doc2[1], distance))
            rankings.sort(key=lambda d: d[2])
            self.stdout.write('\n\n' + title)
            self.stdout.write(repr(stats))
            for d in rankings[0:10]:
                self.stdout.write('\t%s\t%f' % (d[0], d[2]))
                self.stdout.write('\t\t' + repr(d[1]))


def _convert_to_zscores(stats, mean_averages, standard_deviations):
    stats2 = {}
    for key, value in stats.items():
        zscore = (value - mean_averages[key]) / standard_deviations[key]
        stats2[key] = zscore
    return stats2


def _measure_distance(doc1, doc2):
    distance = sum([abs(value - doc2[1][key]) for key, value in doc1[1].items()])
    return distance


def _explain(stats1, stats2, standard_deviations):
    z = ''
    for key, value in stats1.items():
        delta = abs(value - stats2[key])
        z += '%s: %f [%f]\t' % (key, delta, delta / standard_deviations[key])
    return z

