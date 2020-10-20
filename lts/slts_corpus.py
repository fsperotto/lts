import os       # operating system and file operations
import string   # text strings manipulation
import fnmatch  # string search 
import re       # regular expressions
import shutil   # zip
from deprecated import deprecated
from collections.abc import Iterable
from tqdm.auto import tqdm   # progress bar
#from tqdm import tqdm   # progress bar
from nltk import FreqDist
from nltk.tokenize import word_tokenize
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

    def num_paragraphs(self, doc_idx=None):
        if doc_idx is None:
            return len(self.data['paragraphs'])
        else:
            return len(self.data['documents'][doc_idx]['char_paragraph_breakpoints'])+1

            
    def load_documents_from_txt(self, base_folder='./', filefilter='*.txt', append=False, recursive_search=False, single_paragraph_mark=False, breakpoint_mark=DEFAULT_BREAKMARK, verbose=False, tqdm_disable=False):

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

        if verbose:
            print('Files to read: ', inputfilenames)
        
        #read files
        for inputfilename in tqdm(inputfilenames, desc='Reading', unit='files', disable=tqdm_disable):
            with open(inputfilename, "rt", encoding="UTF-8") as inputfile:

                #read raw data from file
                full_text = inputfile.read()

                #replace tabs and strange line markers for a blank
                full_text = re.sub(r'[ \t\v\f\r]+', ' ', full_text)
                #trim lines
                full_text = re.sub(r'\s*\n\s*', '\n', full_text)
                #replace multi linebreaks (>=2) for paragraph_mark '\n\n'
                full_text = re.sub(r'\n\n+', '\n\n', full_text)
                ##breakpoint mark for segment = \n\n\n
                #full_text = re.sub(u'[\n\s]*'+breakpoint_mark+u'[\n\s]*', r'\t\t', full_text)
                full_text = full_text.replace(breakpoint_mark, '\t\t')
                full_text = re.sub(r'\n*\t\t\n*', '\t\t', full_text)
                #strip blanks and empty lines at the beginning and at the end
                full_text = full_text.strip('\s\n')
                
                if single_paragraph_mark:
                    full_text = full_text.replace(r'\n', '\n\n')

                #list of starting positions (in char) for paragraphs
                #pattern = re.compile(r'\t\t', re.UNICODE)                
                pattern = re.compile(r'\t\t')                
                char_seg_breakpoints = [match.end() for match in pattern.finditer(full_text)]
                if len(char_seg_breakpoints) != self.num_breakpoints():
                    print('warning: document ' + inputfilename + ' has different number of segments!')
                
                ##get text segments
                #segments = full_text.split(u'\t\t')
                #
                ##recreate full_text (segment break becomes paragraph break)
                #full_text = u'\n\n'.join(segments)

                full_text = full_text.replace(r'\t\t', '\n\n')
                
                #list of starting positions (in char) for paragraphs
                #pattern = re.compile(r'\n\n', re.UNICODE)                
                pattern = re.compile(r'\n\n')                
                char_paragraph_breakpoints = [match.end() for match in pattern.finditer(full_text)]

                #list of starting positions (in paragraphs) for segments (from the second one)
                paragraph_seg_breakpoints = [char_paragraph_breakpoints.index(pos)+1 for pos in char_seg_breakpoints]
                #paragraph_seg_breakpoints = []
                
                #size of document in characters
                #len_text = len(full_text)
                pattern = re.compile("(?s:.*)$", re.UNICODE)                
                len_text = pattern.search(full_text).end()
                
                
                #create document dictionary
                doc = {'filename':inputfilename, 'text':full_text, 'len_text':len_text, 'char_paragraph_breakpoints':char_paragraph_breakpoints, 'paragraph_segment_breakpoints':paragraph_seg_breakpoints, 'char_segment_breakpoints':char_seg_breakpoints}

                #append to the list
                self.data['documents'].append(doc)
                
        return True

    #returns the string corresponding to the text of a segment, given document index and segment label index
    def get_segment_from_text(self, doc_idx, seg_idx):
        num_breaks = self.num_breakpoints()
        doc = self.data['documents'][doc_idx]
        if seg_idx <= num_breaks:
            #ini = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx-1]-1]    if  seg_idx >= 1           else  0
            #end = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx]-1]      if  seg_idx < num_breaks   else  doc['len_text']
            ini = doc['char_segment_breakpoints'][seg_idx-1]    if  seg_idx >= 1           else  0
            end = doc['char_segment_breakpoints'][seg_idx]      if  seg_idx < num_breaks   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None

    def get_segment_text_from_document(self, doc_idx, seg_idx):
        if 'segments' in self.data['documents']:
            return self.data['documents'][doc_idx]['segments'][seg_idx]['text']
        else:
            return self.get_segment_from_text(doc_idx, seg_idx)
            
    #returns the string corresponding to the text of a paragraph, given document index and paragraph index
    def get_paragraph_from_text(self, doc_idx, par_idx):
        num_paragraphs = self.num_paragraphs(doc_idx=doc_idx)
        doc = self.data['documents'][doc_idx]
        if par_idx < num_paragraphs:
            ini = doc['char_paragraph_breakpoints'][par_idx-1]    if  par_idx >= 1                 else  0
            end = doc['char_paragraph_breakpoints'][par_idx]      if  par_idx < num_paragraphs-1   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None            

    def get_paragraph_text_from_document(self,  doc_idx, par_idx):
        if 'paragraphs' in self.data['documents']:
            return self.data['documents'][doc_idx]['paragraphs'][par_idx]['text']
        else:
            return self.get_paragraph_from_text(doc_idx, par_idx)
            
    def get_paragraph_lbl_idx(self, doc_idx, par_idx):
        num_paragraphs = self.num_paragraphs(doc_idx=doc_idx)
        doc = self.data['documents'][doc_idx]
        if par_idx < num_paragraphs:
            return next(seg_idx for seg_idx, brk_idx in enumerate(doc['paragraph_segment_breakpoints'] + [doc['len_text']]) if par_idx < brk_idx) 
            #return next(seg_idx for seg_idx, brk_idx in enumerate(doc['paragraph_segment_breakpoints']) if par_idx < brk_idx, self.num_labels()-1) 
        else:
            return None            
    
    def get_segment_label(self, lbl_idx):
        return self.data['labels'][lbl_idx]         
            
    def create_segments_list(self, tqdm_disable=False, verbose=False, into_corpus=True, into_docs=True):
        if verbose: 
            print('Creating list of segments...')
        segments = []
        num_labels = self.num_labels()
        for j, doc in enumerate(tqdm(self.data['documents'], desc='Creating list of segments', unit='documents', disable=tqdm_disable)):
            doc_segments = []
            for i in range(num_labels):
                txt = self.get_segment_from_text(j, i)
                seg = {'text':txt, 'lbl_idx':i, 'doc_idx':j}
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
        
            
    def create_paragraphs_list(self, tqdm_disable=False, verbose=False, into_corpus=True, into_docs=True, into_segs=True):
        if verbose: 
            print('Creating list of paragraphs...')
        #initialize full list of paragraphs
        paragraphs = []
        #get the number of breakpoints for segments in this corpus
        num_breaks = self.num_breakpoints()
        for j, doc in enumerate(tqdm(self.data['documents'], desc='Creating list of paragraphs', unit='documents', disable=tqdm_disable)):
            #initialize document list of paragraphs
            doc_paragraphs = []
            for i in range(self.num_paragraphs(j)):
                txt = self.get_paragraph_from_text(j, i)
                #update current segment label
                lbl_idx = self.get_paragraph_lbl_idx(j, i)
                #create the entry relative to this paragraph
                par = {'text':txt, 'lbl_idx':lbl_idx, 'doc_idx':j, 'paragraph_idx':i}
                #append to the document list of paragraphs
                doc_paragraphs.append(par)
            #extended the full list with the document list
            paragraphs.extend(doc_paragraphs)  #note that the object par is the same into both lists
            #if want to create the list into the document, just save the list
            if into_docs: 
                doc['paragraphs'] = doc_paragraphs
        #if want to create the list into the corpus, just save the list
        if into_corpus: 
            self.data['paragraphs'] = paragraphs
        #if want to create the list into the segments, 
        if into_segs:
            #create the empty lists
            for seg in self.data['segments']:
                seg['paragraphs'] = []
            #run over paragraphs into documents and append to segments
            for par in paragraphs:
                doc_idx = par['doc_idx']
                lbl_idx = par['lbl_idx']
                self.data['documents'][doc_idx]['segments'][lbl_idx]['paragraphs'].append(par)
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
        
    def create_vocabulary_list(self, preprocessor_function=_preprocessor_function, tokenizer_function=_tokenizer_function, 
                              into_corpus=True, into_docs=True, into_segs=True,  #into_pars is mandatory
                              tqdm_disable=False, verbose=False):
        if verbose: 
            print("Making full vocabulary... ", end='')
        vocabulary_list = []  #list of retained words, tokenized, but still in order and with repetitions
        #for each paragraph within the corpus
        for par in tqdm(self.data['paragraphs'], desc='Making full vocabulary', unit='paragraphs', disable=tqdm_disable):
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
            vocabulary_list.extend(par['vocabulary_list'])
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
        if into_corpus:
            self.data['vocabulary_list'] = vocabulary_list  #list of retained words, tokenized, but still in order and with repetitions
        #done
        if verbose: 
            print("[DONE] (" + str(len(vocabulary_list)) + ' tokenized words.)')
        return vocabulary_list
            
            
    def create_vocabulary_set(self, preserve_only=None,
                                into_corpus=True, into_docs=True, into_segs=True,  into_pars=True,
                                tqdm_disable=False, verbose=False):
        if verbose: 
            print("Calculating vocabulary frequency... ", end='')    
        if into_corpus:
            self.data['vocabulary_freq'] = FreqDist([voc for voc in tqdm(self.data['vocabulary_list'], desc='Calculating vocabulary frequency on corpus', unit='words', disable=tqdm_disable)])
            if preserve_only is not None:
                self.data['vocabulary_freq'] = self.data['vocabulary_freq'].most_common(preserve_only)
            self.data['vocabulary_set'] = self.data['vocabulary_freq'].keys()
        if into_docs:
            for i, doc in enumerate(tqdm(self.data['documents'], desc='Calculating vocabulary frequency on documents', unit='documents', disable=tqdm_disable)):
                doc['vocabulary_freq'] = FreqDist([voc for voc in doc['vocabulary_list']])
                if preserve_only is not None:
                    doc['vocabulary_freq'] = doc['vocabulary_freq'].most_common(preserve_only)
                doc['vocabulary_set'] = doc['vocabulary_freq'].keys()
        if into_segs:
            for i, seg in enumerate(tqdm(self.data['segments'], desc='Calculating vocabulary frequency on segments', unit='segments', disable=tqdm_disable)):
                seg['vocabulary_freq'] = FreqDist([voc for voc in seg['vocabulary_list']])
                if preserve_only is not None:
                    seg['vocabulary_freq'] = seg['vocabulary_freq'].most_common(preserve_only)
                seg['vocabulary_set'] = seg['vocabulary_freq'].keys()
        if into_pars:
            for i, par in enumerate(tqdm(self.data['paragraphs'], desc='Calculating vocabulary frequency on paragraphs', unit='paragraphs', disable=tqdm_disable)):
                par['vocabulary_freq'] = FreqDist([voc for voc in par['vocabulary_list']])
                #if preserve_only is not None:
                #    par['vocabulary_freq'] = par['vocabulary_freq'].most_common(preserve_only)
                par['vocabulary_set'] = par['vocabulary_freq'].keys()
        if verbose: 
            print("[DONE]")
        
    def create_bow(self, vocabulary_set=None,
                   into_docs=True, into_segs=True, into_pars=True,
                   tqdm_disable=False, verbose=False):
        #get the full vocabulary set
        if vocabulary_set is None: vocabulary_set = self.data['vocabulary_set']
        #bow for documents
        if verbose: print("Making BoW feature set description for segments... ", end='')
        for i, doc in enumerate(tqdm(self.data['documents'], desc='Making bag-of-words representation for documents', unit='documents', disable=tqdm_disable)):
            doc['bow_features'] = [voc in doc['vocabulary_set'] for voc in vocabulary_set]
        if verbose: print("[DONE]")
        #bow for segments
        if verbose: print("Making BoW feature set description for segments... ", end='')
        for i, seg in enumerate(tqdm(self.data['segments'], desc='Making bag-of-words representation for segments', unit='segments', disable=tqdm_disable)):
            seg['bow_features'] = [voc in seg['vocabulary_set'] for voc in vocabulary_set]
            seg['sample'] = (seg['bow_features'], seg['lbl_idx'])
        if verbose: print("[DONE]")
        #bow for paragraphs
        if verbose: print("Making BoW feature set description for segments... ", end='')
        for i, par in enumerate(tqdm(self.data['paragraphs'], desc='Making bag-of-words representation for paragraphs', unit='paragraphs', disable=tqdm_disable)):
            par['bow_features'] = [voc in par['vocabulary_set'] for voc in vocabulary_set]
            par['sample'] = (par['bow_features'], par['lbl_idx'])
        if verbose: print("[DONE]")


#print(" |-Formmating samples... ", end='')        
#data['samples'] = [(segment['features'], segment['label']) for segment in data['segments']]
#print("[DONE]")      


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
