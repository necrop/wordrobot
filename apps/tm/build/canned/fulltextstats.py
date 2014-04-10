
from apps.tm.lib.textmanager import TextManager
from gutenberg.textmanager import TextManager as GutenbergManager

text_ids = (1023, )


def full_text_stats():
    for text_id in text_ids:
        doc = GutenbergManager(text_id)
        docyear = doc.metadata().year
        for para in doc.paragraphs():
            # Process this paragraph
            tm = TextManager(para, docyear)
            antedatings = [l for l in tm.lemmas.lemmas()
                           if l.firstyear > docyear + 5]
            if antedatings:
                print('--------------------------------------------')
                print(para)
                for l in antedatings:
                    print('\t%s\t%s\t%d' % (l.lemma, l.wordclass, l.firstyear))
