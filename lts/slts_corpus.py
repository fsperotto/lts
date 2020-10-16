import os       # operating system and file operations
import string   # text strings manipulation
import fnmatch  # string search 
import re       # regular expressions
import shutil   # zip
from deprecated import deprecated
from collections.abc import Iterable
#from tqdm.notebook import tqdm   # progress bar
from tqdm import tqdm   # progress bar

DEFAULT_BREAKMARK = u'***<-----------------SEGMENT_BREAKPOINT----------------->***'

class SegmentedCorpus:

    def __init__(self, labels, name="corpus", url=None):  
        self.name=name
        self.url=url
        self.data = {'labels':labels}
    
    def num_documents(self):
        return len(self.data['documents']) if  self.data['documents']  else  0
    
    def num_segments(self):
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


    def get_segment_from_text_given_breakpoints(self, document_idx, seg_idx):
        num_breaks = self.num_breakpoints()
        doc = self.data['documents'][document_idx]
        if seg_idx <= num_breaks:
            ini = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx-1]-1]    if  seg_idx >= 1           else  0
            end = doc['char_paragraph_breakpoints'][doc['paragraph_segment_breakpoints'][seg_idx]-1]      if  seg_idx < num_breaks   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None
            
    def get_paragraph_from_text(self, document_idx, par_idx):
        num_paragraphs = self.num_paragraphs(idx_doc=document_idx)
        doc = self.data['documents'][document_idx]
        if par_idx < num_paragraphs:
            ini = doc['char_paragraph_breakpoints'][par_idx-1]    if  par_idx >= 1                 else  0
            end = doc['char_paragraph_breakpoints'][par_idx]      if  par_idx < num_paragraphs-1   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None            

    def get_paragraph_label_idx(self, document_idx, par_idx):
        num_paragraphs = self.num_paragraphs(idx_doc=document_idx)
        doc = self.data['documents'][document_idx]
        if par_idx < num_paragraphs:
            return next(s for s, p in enumerate(doc['paragraph_segment_breakpoints'] + [doc['len_text']]) if par_idx < p) 
        else:
            return None            

    def create_segments_list_into_corpus(self, tqdm_disable=False, verbose=True):
        self.data['segments'] = []
        for j in tqdm(range(self.num_documents())):
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                self.data['segments'].append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})

    def create_segments_list_into_documents(self, tqdm_disable=False, verbose=True):
        for j in tqdm(range(self.num_documents())):
            self.data['documents'][j]['segments'] = []
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                self.data['documents'][j]['segments'].append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})

    def create_segments_list(self, tqdm_disable=False, verbose=True):
        self.data['segments'] = []
        for j in tqdm(range(self.num_documents())):
            self.data['documents'][j]['segments'] = []
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                self.data['documents'][j]['segments'].append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})
            self.data['segments'].append(self.data['documents'][j]['segments'])
            
    def create_paragraphs_list_into_corpus(self, tqdm_disable=False, verbose=True):
        if verbose:
            print('Creating list of paragraphs inside corpus...')
        self.data['paragraphs'] = []
        for j, doc in enumerate(tqdm(self.data['documents'], desc='documents', disable=tqdm_disable)):
            for i in range(self.num_paragraphs(j)):
                txt = self.get_paragraph_from_text(j, i)
                idx = self.get_paragraph_label_idx(j, i)
                self.data['paragraphs'].append({'text':txt, 'segment_index':idx})
        if verbose:
            print('[done]')             
        
    def create_paragraphs_list_into_documents(self, tqdm_disable=False, verbose=True):
        if verbose:
            print('Creating list of paragraphs inside each document...')
        for j in tqdm(range(self.num_documents()), desc='documents', disable=tqdm_disable):
            self.data['documents'][j]['paragraphs'] = []
            for i in range(self.num_paragraphs(j)):
                txt = self.get_paragraph_from_text(j, i)
                idx = self.get_paragraph_label_idx(j, i)
                self.data['documents'][j]['paragraphs'].append({'text':txt, 'segment_index':idx})
        if verbose:
            print('[done]')                 

    def create_paragraphs_list(self, tqdm_disable=False, verbose=True):
        if verbose:
            print('Creating lists of paragraphs...')
        self.data['paragraphs'] = []
        for j in tqdm(range(self.num_documents()), desc='documents', disable=tqdm_disable):
            self.data['documents'][j]['paragraphs'] = []
            for i in range(self.num_paragraphs(j)):
                txt = self.get_paragraph_from_text(j, i)
                idx = self.get_paragraph_label_idx(j, i)
                self.data['documents'][j]['paragraphs'].append({'text':txt, 'segment_index':idx})
            self.data['paragraphs'].append(self.data['documents'][j]['paragraphs'])
        if verbose:
            print('[done]')        
        
    def create_text_files_from_corpus(self, folder='./', segmark = "***<-----------------SEGMENT_BREAKPOINT----------------->***"):
        with open(folder + 'segmark.txt', "wt", encoding="UTF-8") as outputfile:
            outputfile.write(segmark)
        for doc in self.data['documents']:
            full_text = ('\n'+segmark+'\n').join([seg['text'] for seg in doc['segments']])
            with open(folder + doc['filename'], "wt", encoding="UTF-8") as outputfile:
                outputfile.write(full_text)
        shutil.make_archive('corpus', 'zip', folder)

        
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
