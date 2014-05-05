MAX_WORDLENGTH = 500  # Maximum words in a user-submitted piece of text

CORE_WORDS = {'the', 'of', 'and', 'to', 'a', 'in', 'for', 'is', 'on',
              'that', 'by', 'this', 'with', 'you', 'it', 'not', 'or',
              'be', 'are', 'from', 'at', 'as', 'your', 'all', 'have',
              'new', 'more', 'an', 'was', 'we', 'will', 'can',
              'us', 'about', 'if', 'my', 'has', 'but', 'our', 'one',
              'other', 'do', 'no', 'time', 'they', 'he', 'up', 'may',
              'what', 'which', 'their', 'out', 'use', 'any',
              'there', 'see', 'only', 'so', 'his', 'when', 'here',
              'who', 'also', 'now', 'get', 'am', 'been',
              'would', 'how', 'were', 'me', 'some', 'these', 'its',
              'like', 'than', 'into', 'just', 'over', 'very',
              'could', 'should', 'without', 'nor', 'too', 'without',
              'among', 'must', 'where', 'before', 'after', 'them',
              'since'}

CORE_VERBS = {'be', 'do', 'have', 'go', 'get', 'put', 'make', 'can',
              'shall', 'will', 'seem', 'come'}

CALENDAR = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday', 'January', 'February', 'March',
            'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December'}

INDEFINITE_ARTICLES = {'a', 'an', 'some', 'these', 'those'}

INFLECTIONS = {}
for lemma, inflist in [
    ('be', "be, is, am, are, were, was, being, been, 'm, 're, wast, wert, 'twas, wos, woz"),
    ('do', "do, does, did, doing, dost, doth, didst, d'"),
    ('have', "have, has, had, having, hast, hath, hadst, 've, 'd"),
    ('go', 'go, going, gone, goes, went, goest, goeth'),
    ('get', 'get, gets, got, getting'),
    ('make', 'make, makes, made, making'),
    ('run', 'run, runs, ran, running'),
    ('put', 'put, puts, putting'),
    ('eat', 'eat, eats, ate, eating'),
    ('say', 'say, said, says, saying, ses, sez'),
    ("not", "not, n't"),
    ('a', 'a, an'),
    ('may', 'may, might, mightst'),
    ('shall', 'shall, should, shalt, shouldst, sha'),
    ('can', 'can, could, ca, couldst'),
    ('will', "will, would, wo, 'll, wouldst"),
    ('her', "her, 'er"),
    ('him', "him, 'im"),
    ('she', 'she'),
    ('he', 'he'),]:
    for inflection in [i.strip() for i in inflist.split(',')]:
        INFLECTIONS[inflection] = lemma

# These won't be treated as lemmas if preceding a hyphen
PREFIXES = {'non', 'semi', 'anti', 'pro', 'de', 're', 'auto', 'hyper',
            'inter', 'intra', 'meso', 'micro', 'mono', 'mini', 'pan',
            'para', 'multi', 'pseudo', 'para', 'quasi'}

# Count these as wordlike, even though they don't meet the normal criteria
WORDLIKE = {"'re", "'m", "'d", "Mr.", "Mrs."}

PROPER_NAME_BIGRAMS = {
    'United': {'Kingdom', 'States'},
    'New': {'York', 'Zealand', 'England', 'Orleans'},
    'Great': {'Britain', },
    'San': {'Francisco', 'Diego', 'Antonio'},
    'Los': {'Angeles', },
    'Hong': {'Kong', },
    'Soviet': {'Union', },
    'North': {'America', },
    'Santa': {'Lucia', 'Maria', },
    'South': {'America', 'Africa', },
    'Saudi': {'Arabia', },
    'Tierra': {'del', }
}
PROPER_NAME_ENDS = {'Island', 'Islands', 'Sea', 'Ocean', 'Mountain',
                    'Mountains', 'Coast', 'Forest', 'Hill', 'Hills',
                    'Valley', 'City', 'Bay', 'Beach', 'Heights',
                    'Street', 'Road', 'Lane'}
PROPER_NAME_STARTS = {'Lake', 'Mont', 'Mount,'}
PROPER_NAME_TITLES = {'Mr', 'Mr.', 'Mrs', 'Mrs.', 'Miss', 'Ms.', 'Sir',
                      'Lord', 'Lady', 'Captain', 'Capt.', 'Sergeant',
                      'Lieutenant', 'Lieut.', 'Pt.', 'Bp.', 'Abp.',
                      'Revd.', 'Saint', 'St.', 'St', 'Santa', 'Prince',
                      'Princess', 'King', 'Queen'}

CLOSING_PUNCTUATION = {',', ';', ':', '.', ')', ']', '!',
                       '?', '\u201d', '/'}

# Used in JSON packages to avoid bloat
LANGUAGE_ABBREVIATIONS = {'French': 'F', 'Latin': 'L',
                          'Germanic': 'G', 'Romance': 'R',
                          'West Germanic': 'WG', 'Old English': 'OE'}

# Don't attempt to find thesaurus synonyms for these; very likely to
#  be the wrong use or wrong p.o.s.
THESAURUS_BARRED = {'like', 'even',}

SCATTER_BUTTONS = [1750, 1800, 1850, 1900, 1950, 2000]
