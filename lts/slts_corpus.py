import os       # operating system and file operations
import string   # text strings manipulation
import fnmatch  # string search 
import re       # regular expressions

class slts_corpus:

    def __init__(self, labels, name="corpus", url=None):  
        self.name=name
        self.url=url
        self.labels = labels
        self.documents = []
        self.paragraphs = []

    
    def num_documents(self):
        return len(self.documents)
    
    def num_segments(self):
        return len(self.labels)
        
    def num_breakpoints(self):
        return len(self.labels)-1

    def load_documents_from_txt(self, base_folder='./', filefilter='*.txt', append=False, recursive_search=False, breakpoint_mark='***<-----------------SEGMENT_BREAKPOINT----------------->***', paragraph_mark='\n\n', sentence_mark='\n', verbose=True):

        if not append:
            #initialize list of text docs and list of segments inside them
            self.documents = []

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

                #get text segments
                segments = full_text.split(breakpoint_mark)
                for i, segtext in enumerate(segments):
                    #replace tabs and strange line markers for a blank
                    segtext = re.sub(r'[ \t\v\f\r]+', ' ', segtext)
                    #replace multi new lines (>=2) for paragraph_mark
                    segtext = re.sub(r'(\s*\n)+(\s*\n)+\s*', paragraph_mark, segtext)
                    #trim single new lines
                    segtext = re.sub(r'\s*\n\s*', '\n', segtext)
                    #strip blanks and empty lines at the beginning and at the end
                    segments[i] = segtext.strip('\s\n')

                #recreate full_text
                full_text = paragraph_mark.join(segments).strip('\s\n')

                #list of starting positions (in char) for segments
                char_seg_breakpoints = [len(seg)+len(paragraph_mark) for seg in segments[:-1]]
                if len(char_seg_breakpoints) != self.num_breakpoints:
                    print('warning: document ' + inputfilename + ' has different number of segments!')

                #list of starting positions (in char) for paragraphs
                char_paragraph_breakpoints = [m.start() for m in re.finditer(paragraph_mark, full_text)]

                #list of starting positions (in paragraphs) for segments
                #paragraph_seg_breakpoints = [char_paragraph_breakpoints.index(pos) for pos in char_seg_breakpoints]
                paragraph_seg_breakpoints = []

                #create document dictionary
                doc = {'filename':filename, 'text':full_text, 'segments':segments, 'char_paragraph_breakpoints':char_paragraph_breakpoints, 'paragraph_segment_breakpoints':paragraph_seg_breakpoints, 'char_segment_breakpoints':char_seg_breakpoints}

                #append to the list
                self.documents.append(doc)
                
        return True


    def get_segment_from_text_given_breakpoints(self, document_idx, seg_idx):
        num_breaks = self.num_breakpoints()
        if seg_idx <= num_breaks:
            ini = self.documents[document_idx]['paragraph_breakpoints'][self.documents[document_idx]['segment_breakpoints'][seg_idx-1]-1]    if  seg_idx >= 1           else  0
            end = self.documents[document_idx]['paragraph_breakpoints'][self.documents[document_idx]['segment_breakpoints'][seg_idx]-1]      if  seg_idx < num_breaks   else  len(self.documents[document_idx]['text'])
            return self.documents[document_idx]['text'][ini:end].strip('\n\s')
        else:
            return None
            
    def get_paragraph_from_text_given_breakpoints(self, document_idx, par_idx):
        num_breaks = self.num_breakpoints()
        if par_idx <= num_breaks:
            ini = self.documents[document_idx]['paragraph_breakpoints'][par_idx-1]    if  par_idx >= 1           else  0
            end = self.documents[document_idx]['paragraph_breakpoints'][par_idx]      if  par_idx < num_breaks   else  len(self.documents[document_idx]['text'])
            return self.documents[document_idx]['text'][ini:end].strip('\n\s')
        else:
            return None            

            
    def create_corpus_paragraphs_list(self, tqdm_disable=False, verbose=True):
        if verbose:
            print('Creating list of paragraphs inside corpus...')
        self.paragraphs = []
        for j in tqdm(range(len(self.documents)), desc='documents', disable=tqdm_disable):
            lbl_idx=0
            for i in range(self.num_segments):
                txt = get_paragraph_from_text_given_breakpoints(self.documents[j], i)
                self.documents[j]['paragraphs'].append({'text':txt})
                if (i >= self.documents[j]['segment_breakpoints'][lbl_idx]):
                    lbl_idx = min(lbl_idx+1, len(self.documents[j]['segment_breakpoints'])-1)
                self.paragraphs.append({'text':txt, 'lbl_idx':lbl_idx})
        if verbose:
            print('[done]')            
        
    def create_documents_paragraphs_list(self):
        print('Creating list of paragraphs inside each document...')
        for j in tqdm(range(len(self.documents)), desc='documents', disable=tqdm_disable):
            self.documents[j]['paragraphs'] = []
            lbl_idx=0
            for i in range(len(self.documents[j]['paragraph_breakpoints'])+1):
                txt = get_paragraph_from_text_given_breakpoints(self.documents[j], i)
                self.documents[j]['paragraphs'].append({'text':txt})
                if (i >= self.documents[j]['segment_breakpoints'][lbl_idx]):
                    lbl_idx = min(lbl_idx+1, len(self.documents[j]['segment_breakpoints'])-1)
                self.paragraphs.append({'text':txt, 'lbl_idx':lbl_idx})
        print('[done]')            