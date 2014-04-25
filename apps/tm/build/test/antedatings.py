
from apps.tm.lib.textmanager import TextManager
from gutenberg.textmanager import TextManager as GutenbergManager

text_ids = (6593, )


def full_text_stats():
    for text_id in text_ids:
        doc = GutenbergManager(text_id)
        print('===========================================================')
        print(doc.citation())
        print('===========================================================')
        docyear = doc.metadata.year
        for para in doc.paragraphs():
            # Process this paragraph
            tm = TextManager(para, docyear)
            antedatings = [l for l in tm.lemmas.lemmas()
                           if l.firstyear > docyear + 5]
            if antedatings:
                print('--------------------------------------------')
                print(para, '\n\n')
                for l in antedatings:
                    sentence = ''
                    for token in tm.tokens:
                        if token.is_matched_to_lemma(l):
                            sentence = token.sentence
                    print(sentence)
                    print('\t%s\t%s\t%d' % (l.lemma, l.wordclass, l.firstyear))
