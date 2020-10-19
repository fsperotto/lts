import os       # operating system and file operations
import string   # text strings manipulation
import fnmatch  # string search 
import re       # regular expressions
import shutil   # zip
from deprecated import deprecated
from collections.abc import Iterable
from tqdm.notebook import tqdm   # progress bar
from nltk import FreqDist
from nltk.tokenize import word_tokenize
#from tqdm import tqdm   # progress bar
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

DEFAULT_BREAKMARK = u'***<-----------------SEGMENT_BREAKPOINT----------------->***'

def _preprocessor_function(text): 
    if text is None: text = ""
    REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
    BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
    ONLY_WORDS_RE = re.compile(r"\w+")
    STOPWORDS = set(stopwords.words('french'))
    # lowercase text
    text = text.lower()
    # replace REPLACE_BY_SPACE_RE symbols by space in text. substitute the matched string in REPLACE_BY_SPACE_RE with space.
    text = REPLACE_BY_SPACE_RE.sub(' ', text) 
    # remove symbols which are in BAD_SYMBOLS_RE from text. substitute the matched string in BAD_SYMBOLS_RE with nothing. 
    text = BAD_SYMBOLS_RE.sub('', text) 
    #text = re.sub(r'\W+', '', text)
    text = text.replace('\d+', '')
    #remove stopwords
    text = ' '.join(word for word in text.split() if word not in STOPWORDS) # remove stopwors from text
    return text            
        
def _tokenizer_function(text): 
    if text is None: text = ""
    ## using spaces    
    #return  text.split()
    ## using regex   
    #return  re.split(r'\W+', text)
    # using french word tokenizer from nltk
    return word_tokenize(text, language='french')


    
class SegmentedCorpus:

    def __init__(self, labels, name="corpus", url=None):  
        self.name=name
        self.url=url
        self.data = {'labels':labels}
    
    def num_documents(self):
        return len(self.data['documents']) if  self.data['documents']  else  0
    
    def num_labels(self):
        return len(self.data['labels'])  if  self.data['labels']  else  0
        
    def num_breakpoints(self):
        return len(self.data['labels'])-1  if  self.data['labels']  else  0

    def num_paragraphs(self, idx_doc=None):
        if idx_doc is None:
            return len(self.data['paragraphs'])
        else:
            return len(self.data['documents'][idx_doc]['char_paragraph_breakpoints'])+1

            
    def load_documents_from_txt(self, base_folder='./', filefilter='*.txt', append=False, recursive_search=False, single_paragraph_mark=False, breakpoint_mark=DEFAULT_BREAKMARK, verbose=True):

        if (not append) or (not 'documents' in self.data.keys()) or (not isinstance(self.data['documents'], Iterable)):
            #initialize list of text docs and list of segments inside them
            self.data['documents'] = []

        #create a list of path+filenames to read
        inputfilenames = []
        #for each subdirectory in the base directory
        for path, dirs, files in os.walk(os.path.abspath(base_folder)):
            #for each file corresponding to the filter
            for filename in fnmatch.filter(files, filefilter):
                inputfilenames.append(os.path.join(base_folder, os.path.join(path, filename)))
            if not recursive_search:
                break

        #if verbose:
        #    print(inputfilenames)
        
        #read files
        for inputfilename in inputfilenames:
            with open(inputfilename, "rt", encoding="UTF-8") as inputfile:

                #read raw data from file
                full_text = inputfile.read()

                #replace tabs and strange line markers for a blank
                full_text = re.sub(u'[ \t\v\f\r]+', ' ', full_text)
                #trim lines
                full_text = re.sub(u'\s*\n\s*', u'\n', full_text)
                #replace multi linebreaks (>=2) for paragraph_mark '\n\n'
                full_text = re.sub(u'\n\n+', u'\n\n', full_text)
                ##breakpoint mark for segment = \n\n\n
                #full_text = re.sub(u'[\n\s]*'+breakpoint_mark+u'[\n\s]*', r'\t\t', full_text)
                full_text = full_text.replace(breakpoint_mark, u'\t\t')
                full_text = re.sub(u'\n*\t\t\n*', u'\t\t', full_text)
                #strip blanks and empty lines at the beginning and at the end
                full_text = full_text.strip(u'\s\n')
                
                if single_paragraph_mark:
                    full_text = full_text.replace(u'\n', u'\n\n')

                #list of starting positions (in char) for paragraphs
                pattern = re.compile(u'\t\t', re.UNICODE)                
                char_seg_breakpoints = [match.end() for match in pattern.finditer(full_text)]
                if len(char_seg_breakpoints) != self.num_breakpoints():
                    print('warning: document ' + inputfilename + ' has different number of segments!')
                
                ##get text segments
                #segments = full_text.split(u'\t\t')
                #
                ##recreate full_text (segment break becomes paragraph break)
                #full_text = u'\n\n'.join(segments)

                full_text = full_text.replace(u'\t\t', u'\n\n')
                
                #list of starting positions (in char) for paragraphs
                pattern = re.compile(u'\n\n', re.UNICODE)                
                char_paragraph_breakpoints = [match.end() for match in pattern.finditer(full_text)]

                #list of starting positions (in paragraphs) for segments (from the second one)
                paragraph_seg_breakpoints = [char_paragraph_breakpoints.index(pos) for pos in char_seg_breakpoints]
                #paragraph_seg_breakpoints = []
                
                #size of document in characters
                #len_text = len(full_text)
                pattern = re.compile("(?s:.*)$", re.UNICODE)                
                len_text = pattern.search(full_text).end()
                
                
                #create document dictionary
                doc = {'filename':filename, 'text':full_text, 'len_text':len_text, 'char_paragraph_breakpoints':char_paragraph_breakpoints, 'paragraph_segment_breakpoints':paragraph_seg_breakpoints, 'char_segment_breakpoints':char_seg_breakpoints}

                #append to the list
                self.data['documents'].append(doc)
                
        return True


    def get_segment_from_text(self, document_idx, seg_idx):
        num_breaks = self.num_breakpoints()
        doc = self.data['documents'][document_idx]
        if seg_idx <= num_breaks:
            ini = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx-1]-1]    if  seg_idx >= 1           else  0
            end = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx]-1]      if  seg_idx < num_breaks   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None

    def get_segment_text_from_document(self, document_idx, seg_idx):
        if 'segments' in self.data['documents']:
            return self.data['documents'][document_idx]['segments'][seg_idx]['text']
        else:
            return self.get_segment_from_text(document_idx, seg_idx)
            
    def get_paragraph_from_text(self, document_idx, par_idx):
        num_paragraphs = self.num_paragraphs(idx_doc=document_idx)
        doc = self.data['documents'][document_idx]
        if par_idx < num_paragraphs:
            ini = doc['char_paragraph_breakpoints'][par_idx-1]    if  par_idx >= 1                 else  0
            end = doc['char_paragraph_breakpoints'][par_idx]      if  par_idx < num_paragraphs-1   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None            

    def get_paragraph_text_from_document(self, document_idx, par_idx):
        if 'paragraphs' in self.data['documents']:
            return self.data['documents'][document_idx]['paragraphs'][par_idx]['text']
        else:
            return self.get_paragraph_from_text(document_idx, seg_idx)
            
    def get_paragraph_label_idx(self, document_idx, par_idx):
        num_paragraphs = self.num_paragraphs(idx_doc=document_idx)
        doc = self.data['documents'][document_idx]
        if par_idx < num_paragraphs:
            return next(s for s, p in enumerate(doc['paragraph_segment_breakpoints'] + [doc['len_text']]) if par_idx < p) 
        else:
            return None            
    
    def get_segment_label(self, label_idx):
        return self.data['labels'][label_idx]         
            
    def create_segments_list(self, tqdm_disable=False, verbose=True, into_corpus=True, into_docs=True):
        if verbose: 
            print('Creating list of segments...')
        segments = []
        num_labels = self.num_labels()
        for j, doc in enumerate(tqdm(self.data['documents'], desc='documents', disable=tqdm_disable)):
            doc_segments = []
            for i in range(num_labels):
                txt = self.get_segment_from_text(j, i)
                seg = {'text':txt, 'label_index':i, 'document_index':j}
                doc_segments.append(seg)   
            segments.extend(doc_segments)  #note that the object seg is the same into both lists
            if into_docs: 
                doc['segments'] = doc_segments
        if into_corpus:
            self.data['segments'] = segments
        if verbose: 
            print('[done]')        
        return segments
    # see: itertools.chain(*iterables) ?
        
            
    def create_paragraphs_list(self, tqdm_disable=False, verbose=True, into_corpus=True, into_docs=True, into_segs=True):
        if verbose: 
            print('Creating list of paragraphs...')
        paragraphs = []
        num_breaks = self.num_breakpoints()
        for j, doc in enumerate(tqdm(self.data['documents'], desc='documents', disable=tqdm_disable)):
            doc_paragraphs = []
            lbl_idx = 0
            for i in range(self.num_paragraphs(j)):
                txt = self.get_paragraph_from_text(j, i)
                #lbl_idx = self.get_paragraph_label_idx(j, i)
                if (i < num_breaks) and (i == doc['paragraph_segment_breakpoints'][lbl_idx]):
                    lbl_idx += 1
                par = {'text':txt, 'label_index':lbl_idx, 'document_idx':j, 'paragraph_idx':i}
                doc_paragraphs.append(par)
            paragraphs.extend(doc_paragraphs)  #note that the object par is the same into both lists
            if into_docs: 
                doc['paragraphs'] = doc_paragraphs
        if into_corpus: 
            self.data['paragraphs'] = paragraphs
        if verbose: 
            print('[done]')        
        return paragraphs
        
        
    def create_text_files_from_corpus(self, folder='./', segmark=DEFAULT_BREAKMARK):
        with open(folder + 'segmark.txt', "wt", encoding="UTF-8") as outputfile:
            outputfile.write(segmark)
        for doc in self.data['documents']:
            full_text = ('\n'+segmark+'\n').join([seg['text'] for seg in doc['segments']])
            with open(folder + doc['filename'], "wt", encoding="UTF-8") as outputfile:
                outputfile.write(full_text)
        shutil.make_archive('corpus', 'zip', folder)

    #print('\n\n*************************************************\n')
    #print("Getting vocabulary... ")       
    #
    #voc_pickel_file = "voc.pickle"
    #!rm {voc_pickel_file}
    #
    ##if a pickle file exists, read it
    #if os.path.isfile(WORKING_FOLDER + voc_pickel_file):
    #    print(" |-Reading pickle file... ", end='')        
    #    with open(WORKING_FOLDER + voc_pickel_file, 'rb') as fp:
    #        data['vocabulary'] = pickle.load(fp)
    #    print("[DONE]")      
    #
    #else:
    #    print(" |-Pre-processing texts and creating vocabulary... ", end='')        
    #    data['vocabulary'] = vocabularize_all([doc['text'] for doc in data['documents']])
    #    print("[DONE]")
    #    print(" |-Saving pickle file... ", end='')
    #    with open(WORKING_FOLDER + voc_pickel_file, 'wb') as fp:
    #        pickle.dump(data['vocabulary'], fp, protocol=pickle.HIGHEST_PROTOCOL)            
    #    print("[DONE]")
        
    def create_vocabulary(self, preprocessor_function=_preprocessor_function, tokenizer_function=_tokenizer_function, 
                          into_docs=True, into_segs=True, 
                          tqdm_disable=False, verbose=True):
        if verbose: 
            print("Making full vocabulary... ", end='')
        self.data['vocabulary_list'] = []  #list of retained words, tokenized, but still in order and with repetitions
        #for each paragraph within the corpus
        for par in tqdm(self.data['paragraphs'], desc='paragraphs', disable=tqdm_disable):
            #get clean text of paragraph
            if preprocessor_function is not None:
                text = preprocessor_function(par['text'])
            else:
                text = par['text']
            #get list of tokens (vocabulary on paragraph)
            if preprocessor_function is not None:
                par['vocabulary_list'] = tokenizer_function(text)
            else:
                par['vocabulary_list'] = text.split()
            #insert into corpus
            self.data['vocabulary_list'].extend(par['vocabulary_list'])
        #document vocabulary
        if into_docs: 
            for doc in tqdm(self.data['documents'], desc='documents', disable=tqdm_disable):
                doc['vocabulary_list'] = []
                for par in doc['paragraphs']:
                    doc['vocabulary_list'].extend(par['vocabulary_list'])
        #segment vocabulary
        if into_segs: 
            for seg in tqdm(self.data['segments'], desc='segments', disable=tqdm_disable):
                seg['vocabulary_list'] = []
                for par in seg['paragraphs']:
                    seg['vocabulary_list'].extend(par['vocabulary_list'])
        #done
        if verbose: 
            print("[DONE] (" + str(len(self.data['vocabulary_list'])) + ' tokenized words.)')
        return self.data['vocabulary_list']
            
            
    def create_vocabulary_frequency(self, tqdm_disable=False, verbose=True, preserve_only=None):
        if verbose: 
            print("Calculating vocabulary frequency... ", end='')    
        self.data['vocabulary_freq'] = FreqDist([voc for voc in self.data['vocabulary_list']])
        if preserve_only is not None:
            self.data['vocabulary_freq'] = corpus.data['voc_freq'].most_common(preserve_only)
            self.data['vocabulary_set'] = self.data['voc_freq'].keys()
        if verbose: print("[DONE]")
        
    def create_vocabulary_frequency_on_segments(self, tqdm_disable=False, verbose=True, preserve_only=None):
        if verbose: print(" |-Making segment vocabulary... ", end='')
        for i, seg in enumerate(tqdm(self.data['segments'])):
            self.data['segments'][i]['voc_freq'] = FreqDist([voc for voc in self.data['vocabulary']])
            text = seg['text']
            if text is not None:
                text = text.lower()
            else:
                text = ""
            all_words = TextPreProcessor.removeNoise(text.split())
            tokenized_words = TextPreProcessor.tokenize(all_words)
            self.data['segments'][i]['voc_freq'] = FreqDist([voc for voc in tokenized_words])
            self.data['segments'][i]['vocabulary'] = self.data['segments'][i]['voc_freq'].keys()
        if verbose: print("[DONE]")      
            
#about space special characters
#
#charset = {'\\v (Vertical Tab)':'\v', 
#           '\\t (Horizontal Tab)':'\t', 
#           '\\r (Carriage Return)':'\r',
#           '\\n (Line Feed)':'\n', 
#           '\\f (form feed)':'\f',
#           '\\b (Backspace)':'\b',
#           '\\a (Bell Alert)':'\a',
#           '\\e (Escape)':'\e'}
#
#for c in charset.keys():
#    print(c + ' ASCII[' + str(ord(charset[c])) + "]:\n" + "hello" + charset[c] + "world")
#    print('isspace() = ' + str(charset[c].isspace()))
#    print()
#
#\v (Vertical Tab) ASCII[11]:
#helloworld
#isspace() = True
#
#\t (Horizontal Tab) ASCII[9]:
#hello	world
#isspace() = True
#
#\r (Carriage Return) ASCII[13]:
#world
#isspace() = True
#
#\n (Line Feed) ASCII[10]:
#hello
#world
#isspace() = True
#
#\f (form feed) ASCII[12]:
#helloworld
#isspace() = True
#
#\b (Backspace) ASCII[8]:
#hellworld
#isspace() = False
#
#\a (Bell Alert) ASCII[7]:
#helloworld
#isspace() = False
#
