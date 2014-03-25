
import datetime
import re

from django.utils.text import normalize_newlines

from ..models import UserSubmission
from . import appsettings as local_settings

max_words = local_settings.MAX_WORDLENGTH


def submission_cleaner(post):
    for key in ('author', 'title', 'year', 'text'):
        post[key] = post[key].strip().replace('>', '.').replace('<', '.')

    if post['title']:
        max_length = UserSubmission._meta.get_field('title').max_length
        post['title'] = post['title'][:max_length]
    else:
        post['title'] = 'Untitled'

    if post['author']:
        max_length = UserSubmission._meta.get_field('author').max_length
        post['author'] = post['author'][:max_length]
    else:
        post['author'] = ''

    current_year = datetime.date.today().year
    try:
        year = int(post['year'])
    except ValueError:
        year = current_year
    if year < 1500 or year > current_year:
        year = current_year
    post['year'] = year

    post['text'] = _trim_text(post['text'])
    return post


def _trim_text(text):
    text = normalize_newlines(text)
    lines = [l.replace('\t', ' ').strip() for l in text.split('\n')]
    lines = [re.sub(r'  +', r' ', l) for l in lines]
    lines = [l for l in lines if l]

    # Ditch any lines beyond the maximum wordcount
    lines2 = []
    running_total = 0
    for line in lines:
        lines2.append(line)
        running_total += len(line.split(' '))
        if running_total > max_words:
            break

    # Trim the last line if necessary
    if running_total > max_words * 1.1:
        lastwords = lines2.pop().split(' ')
        running_total = sum([len(l.split(' ')) for l in lines2])
        gap = max_words - running_total
        if gap > 5:
            lastline = ' '.join(lastwords[:gap])
            lines2.append(lastline)

    return '\n'.join(lines2)

