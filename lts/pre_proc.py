#####################################
# NLP pre-processing text methods
#####################################

# dependencies
import re       # regular expressions
import string   # text strings manipulation
import fnmatch  # string search 
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# define default language
LANG = 'french'

class TextPreProcessor:

    # eliminate blank lines (using regex)
    @staticmethod
    def sanitize(text):
        #replace tabs and strange line markers for a blank
        text = re.sub(r'[ \t\v\f\r]+', ' ', text)
        #replace multi new lines for single new line
        text = re.sub(r'\s*\n\s*', '\n', text)
        #strip blanks and empty lines at the beginning and at the end
        text = text.strip()
        text = text.strip('\s')
        #remove new lines at the beginning and at the end
        text = text.strip('\n')
        #text = re.sub(r'^\n+', '', text)
        #text = re.sub(r'\n+$', '', text)
        #replace new lines inside sentence for a blank
        text = re.sub(r'([a-zA-Z0-9ãâàéèëïîöôõuüû])\n([a-zãâàéèëïîöôõuüû])', r'\1 \2', text)
        text = re.sub(r'([A-Z])\n([A-Z])', r'\1 \2', text)
        #return modified text
        return text


    #########################################

    # split based on words
    @staticmethod
    def split_words(text, language=LANG):
        ## using spaces    
        #return  text.split()
        ## using regex   
        #return  re.split(r'\W+', text)
        # using word tokenizer (nltk)
        return word_tokenize(text, language)


    # split paragraphs (using regex)
    @staticmethod
    def split_paragraphs(text, separator='\n'):
        return text.strip().split(separator)
        #return re.split(r'[\r\n]+', text)
        #return re.split(r'\n', text)
        
    # sentence tokenizer (nltk)
    def splitSentences(text, language=LANG):
        return sent_tokenize(text, language)

    #########################################

    @staticmethod
    def vocabularize_all(texts):
        words = []
        for text in tqdm(texts):
            words.extend(splitWords(text))
        vocabulary = tokenize(words)
        return vocabulary

    @staticmethod
    def vocabularize(text):
        text = sanitize(text)
        text_words = splitWords(text)
        text_vocabulary = tokenize(text_words)
        return text_vocabulary

    #########################################

    @staticmethod
    def tokenize(words, language=LANG, bremoveNonAlpha=True, bforceLowerCase=True, bremoveNoise=True, bstemWords=True, bmakeVocabulary=False):
        if bremoveNonAlpha:
            tokens = removeNonAlpha(words)
        if bforceLowerCase:
            tokens = forceLowerCase(tokens)
        if bremoveNoise:
            tokens = removeNoise(tokens, language)
        if bstemWords:
            tokens = stemWords(tokens, language)
        if bmakeVocabulary:
            tokens = makeVocabulary(tokens)
        return tokens
        
    #---------------------------------------

    # remove stop words and punctuation from each word
    @staticmethod
    def removeNoise(words, language=LANG, min_len=3):
        noise = stopwords.words(language) + list(string.punctuation)
        return [w for w in words if w not in noise and len(w) >= min_len]

    # convert to lower case
    @staticmethod
    def forceLowerCase(words):
        return [word.lower() for word in words]

    # remove all tokens that are not alphabetic
    @staticmethod
    def removeNonAlpha(words):
        return [word for word in words if word.isalpha()]

    # stemming of words
    @staticmethod
    def stemWords(words, language=LANG):
        stemmer = SnowballStemmer(language)    
        #porter = PorterStemmer()
        return [stemmer.stem(word) for word in words]

    # remove stopwords
    @staticmethod
    def removeStopWords(words, language=LANG):
        stop_words = stopwords.words(language)
        return [w for w in words if w not in stop_words]

    # remove punctuation from each word
    @staticmethod
    def removePonctuation(words):
        table = str.maketrans('', '', string.punctuation)
        return [w.translate(table) for w in words]

    # list of words to ordered set
    @staticmethod
    def makeVocabulary(words):
        return sorted(set(words))

    #########################################

    #from: https://towardsdatascience.com/multi-class-text-classification-with-lstm-1590bee1bd17
    REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
    BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
    ONLY_WORDS_RE = re.compile(r"\w+")
    STOPWORDS = set(stopwords.words(LANG))
    #display(df(STOPWORDS))

    @staticmethod
    def clean_text(text):
    #Remove digits in text.
        text = text.lower() # lowercase text
        text = REPLACE_BY_SPACE_RE.sub(' ', text) # replace REPLACE_BY_SPACE_RE symbols by space in text. substitute the matched string in REPLACE_BY_SPACE_RE with space.
        text = BAD_SYMBOLS_RE.sub('', text) # remove symbols which are in BAD_SYMBOLS_RE from text. substitute the matched string in BAD_SYMBOLS_RE with nothing. 
        #text = text.replace('x', '')
        #text = re.sub(r'\W+', '', text)
        text = text.replace('\d+', '')
        #text = ' '.join(word for word in text.split() if word not in STOPWORDS) # remove stopwors from text
        return text