import os       # operating system and file operations
import string   # text strings manipulation
import fnmatch  # string search 
import re       # regular expressions
from deprecated import deprecated
from collections.abc import Iterable
from tqdm.notebook import tqdm   # progress bar

class SegmentedCorpus:
   
    def __init__(self, labels=[['seg_a','seg_b'], None, None, None], name="corpus", url=None, hierarchy_names=['segment', 'paragraph', 'sentence', 'word'], break_char_marks=['\f', '\v', '\n', ' ']):  
        self.name=name
        self.url=url
        self.hierarchy_names = hierarchy_names
        self.break_char_marks = break_char_marks
        self.labels = labels
        self.documents = []
    
    def num_levels(self):
        return len(self.hierarchy_names)

    def num_segments(self, level=0):
        return len(self.labels[level])

    def num_breakpoints(self, level=0):
        return len(self.labels[level]-1)

    def num_documents(self):
        return len(self.documents)
    

    @staticmethod
    def get_break_positions(text, breakpoint_regex_marks):
        #recursively for each hierarchical segmentation level
        for regex_mark in breakpoint_regex_marks:
            #list of starting positions (in char)
            pattern = re.compile(regex_mark, re.UNICODE)                
            breakpoints = [match.end() for match in pattern.finditer(text)]
    
    
    def load_documents_from_txt(self, base_folder='./', filefilter='*.txt', append=False, recursive_search=False, breakpoint_regex_marks=[r'\s*\*\*\*<-----------------SEGMENT_BREAKPOINT----------------->\*\*\*\s*', r'\s*\n\s*'], verbose=True, encoding="UTF-8"):

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

        #read files
        for inputfilename in inputfilenames:
            with open(inputfilename, "rt", encoding=encoding) as inputfile:

                if verbose:
                    print('reading ' + inputfilename, end=' ')

                #read raw data from file
                full_text = inputfile.read()

                #initial state of breakpoints, will be replaced hierarchically by lists of lists
                ini = 0
                #end = len(full_text)-1
                pattern = re.compile(r'$', re.UNICODE)                
                match = pattern.search(full_text[::-1])
                end = match.start()-1  # same than match.end() because pattern is single character
                absolute_segments = [[[ini, end]]]   #positions: start character of text, end character of text
                absolute_breakpoints = [[[]]]
                relative_segments = [[[ini, end]]]   #positions: start character of text, end character of text
                relative_breakpoints = [[[]]]
                
                #for each hierarchical segmentation level
                for level, regex_mark in enumerate(breakpoint_regex_marks):
                    #append new level
                    absolute_segments.append([])
                    absolute_breakpoints.append([])
                    relative_segments.append([])
                    relative_breakpoints.append([])
                    for i, seg in enumerate(absolute_segments):
                        #list of starting positions (in char)
                        ini, end = seg
                        pattern = re.compile(regex_mark, re.UNICODE)
                        rel_breaks = [ [match.start(), match.end()] for match in pattern.finditer(full_text[ini:end+1]) ]
                        abs_breaks = [ [rel_ini+ini, rel_end+end] for rel_ini, rel_end in rel_breaks]
                        relative_breakpoints[level+1].append([rel_breaks])
                        absolute_breakpoints[level+1].append(seg_breakpoints)
                    
                    
                    

                #replace tabs and strange line markers for a blank
                #full_text = re.sub(u'[ \t\v\f\r]+', ' ', full_text)
                full_text = re.sub(u'[ \t\v\f\r\b\a\e]+', ' ', full_text)
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

                #list of starting positions (in paragraphs) for segments
                paragraph_seg_breakpoints = [char_paragraph_breakpoints.index(pos) for pos in char_seg_breakpoints]
                #paragraph_seg_breakpoints = []
                
                #size of document in characters
                len_text = len(full_text)
                
                #create document dictionary
                doc = {'filename':filename, 'text':full_text, 'len_text':len_text, 'char_paragraph_breakpoints':char_paragraph_breakpoints, 'paragraph_segment_breakpoints':paragraph_seg_breakpoints, 'char_segment_breakpoints':char_seg_breakpoints}

                #append to the list
                self.data['documents'].append(doc)

                if verbose:
                    print('[DONE]')
                
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
            
    def get_paragraph_from_text_given_breakpoints(self, document_idx, par_idx):
        num_breaks = self.num_breakpoints()
        doc = self.data['documents'][document_idx]
        if par_idx <= num_breaks:
            ini = doc['char_paragraph_breakpoints'][par_idx-1]    if  par_idx >= 1           else  0
            end = doc['char_paragraph_breakpoints'][par_idx]      if  par_idx < num_breaks   else  doc['len_text']
            return doc['text'][ini:end].strip('\n\s')
        else:
            return None            


    def create_segments_list_into_corpus(self, tqdm_disable=False, verbose=True):
        segments = []
        for j in tqdm(range(self.num_documents())):
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                segments.append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})
        self.data['segments'] = segments

    def create_segments_list_into_documents(self, tqdm_disable=False, verbose=True):
        segments = []
        for j in tqdm(range(self.num_documents())):
            doc_segments = []
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                doc_segments.append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})
            self.data['documents'][j]['segments'] = doc_segments

    def create_segments_list(self, tqdm_disable=False, verbose=True):
        for j in tqdm(range(self.num_documents())):
            doc_segments = []
            for i in range(self.num_segments()):
                txt = self.get_segment_from_text_given_breakpoints(j, i)
                doc_segments.append({'text':txt, 'segment_index':i, 'segment_label':self.data['labels'][i]})
            self.data['documents'][j]['segments'] = doc_segments
            segments.append(doc_segments)
        self.data['segments'] = segments
            
    def create_corpus_paragraphs_list(self, tqdm_disable=False, verbose=True):
        if verbose:
            print('Creating list of paragraphs inside corpus...')
        self.data['paragraphs'] = []
        for j, doc in enumerate(tqdm(self.data['documents'], desc='documents', disable=tqdm_disable)):
            for i in range(self.num_segments()):
                txt = self.get_paragraph_from_text_given_breakpoints(doc, i)
                self.data['paragraphs'].append({'text':txt})
        if verbose:
            print('[done]')            
        
    def create_documents_paragraphs_list(self):
        print('Creating list of paragraphs inside each document...')
        for j in tqdm(range(len(self.documents)), desc='documents', disable=tqdm_disable):
            self.documents[j]['paragraphs'] = []
            lbl_idx=0
            for i in range(len(self.documents[j]['paragraph_breakpoints'])+1):
                txt = self.get_paragraph_from_text_given_breakpoints(self.documents[j], i)
                self.documents[j]['paragraphs'].append({'text':txt})
                if (i >= self.documents[j]['segment_breakpoints'][lbl_idx]):
                    lbl_idx = min(lbl_idx+1, len(self.documents[j]['segment_breakpoints'])-1)
                self.paragraphs.append({'text':txt, 'lbl_idx':lbl_idx})
        print('[done]')            
        
        
        
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
