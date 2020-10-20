import re

#----------------------
# ABSTRACT SEGMENTER CLASS
#----------------------

class Segmenter:
    
    def __init__(self, num_segs, name="Segmenter"):
        self.name = name
        self.num_segs = num_segs
        self.num_breaks = num_segs-1

        
    def classify(self, features=None, segment=None, text=None):
        
        if features is None:
            if segment is not None and 'features' in segment:
                features = segment['features']
            else:
                if text is None:
                    raise("Error: segmenter needs at least one of the following parameters: 1) paragraphs, or 2) document, or 3) text.")
                else:
                    return self._classify_text(text)
        else:
            return self._classify_features(features) 

    
    def _classify_text(self, text):
        #raise("calling abstract class method.")
        return None
    
    
    def _classify_features(self, features):
        #raise("calling abstract class method.")
        return None

    def learn(self, data):
        #raise("calling abstract class method.")
        pass
    
        
    def segment(self, text=None, paragraphs=None, document=None):
  
        if paragraphs is None:
            if document is not None and 'paragraphs' in document:
                paragraphs = document['paragraphs']
            else:
                if text is None:
                    raise("Error: segmenter needs at least one of the following parameters: 1) paragraphs, or 2) document, or 3) text.")
                else:
                    paragraphs = text.split('\n')
                    
        return self._segment_paragraphs(paragraphs)
        
    def _segment_paragraphs(self, paragraphs):
        raise("calling abstract class method.")

#    def _segment_text(self, text):
#        raise("calling abstract class method.")

        
#########################################################################################

############
# CONSTANTS
############

# xml labels
LAB_HEAD = 'headerCA'
LAB_FACT = 'faitsCA'
LAB_REAS = 'motifsCA'
LAB_CONC = 'conclusionCA'

IDX_HEAD = 0
IDX_FACT = 1
IDX_REAS = 2
IDX_CONC = 3

idx_to_lab = lambda idx: [LAB_HEAD, LAB_FACT, LAB_REAS, LAB_CONC][idx]
lab_to_idx = lambda lab: {LAB_HEAD:IDX_HEAD, LAB_FACT:IDX_FACT, LAB_REAS:IDX_REAS, LAB_CONC:IDX_CONC}[lab] 

#----------------------
# FADILA SEGMENTER
#----------------------
# Set of rules defined by FADILA TALEB pour for segmenting Court of Appeal decisions
#  in 4 segments: header, facts, reasons, and conclusion

#RegEx rules
fadRegEx = [re.compile(r'^\s*(Expos[eé] du [Ll]itige|EXPOS[EÉ] DU LITIGE|Expos[eé] des faits|EXPOS[EÉ] DES FAITS|(Vu|VU) (que|QUE|le jugement)|Faits|FAITS|Par [Aa]ctes|PAR ACTES)', re.MULTILINE),
            re.compile(r'^\s*(Sur [Cc]e|SUR CE|Sur [Qq]uoi|SUR QUOI|(Cela|Ceci) étant|(CECI|CELA) ([EÉeé]tant|[EÉ]TANT)|[EÉeé]tant [Ee]xpos[eé]|[EÉ]TANT EXPOS[EÉ]|Ce [Ss]ur [Qq]uoi|CE SUR QUOI|Motifs|MOTIFS|(La [Cc]our|LA COUR)[ : a-z]* attendu que)', re.MULTILINE),
            re.compile(r'^\s*((Par [Cc]es [Mm]otifs|PAR CES MOTIFS)|(D[eé]cision|DECISION))', re.MULTILINE)]


class RegexSegmenter(Segmenter):
    
    def __init__(self, num_segs, regex_rules=fadRegEx, name="Regex"):
        super().__init__(num_segs, name=name)
        self.regex_rules = regex_rules

    # classify a piece of text using EXPERT rules
    def _classify_text(self, text):
        #this method can only identify the begining of FACTS, REASONS or CONCLUSIONS segments (i.e. only the first paragraph after a segment break)
        
        #search
        for lbl_idx, pattern in enumerate(self.regex_rules):
            if pattern.search(text):
                return lbl_idx

        #default value is NONE
        return None
            
    
    # segment a document using rules
    def _segment_paragraphs(self, paragraphs):
  
        #for each break get the corresponding regex, then try to match each regex to each paragraph
        confidence = [ [1.0  if pattern.search(par) is not None  else  0.0  for  par in paragraphs] for pattern in self.regex_rules ]

        #get the first occurrence as suggestion
        breakpoints = [ next(par_idx for par_idx, confidence_value in enumerate(confidence[lbl_idx]) if confidence_value == 1.0 ) for lbl_idx in range(len(self.regex_rules)) ]

        return breakpoints, confidence
    
  
class SizeSegmenter(Segmenter):

    #constructor
    def __init__(self, num_segs, strategy='ratio', name=None):
        super().__init__(num_segs, name=name)
        #self.avg = {FAD_HEAD:0.0, FAD_FACT:0.0, FAD_REAS:0.0, FAD_CONC:0.0}
        if name is None:
            self.name = f"Size Segmenter ({strategy})"
        self.avg = []
        self.strategy = strategy
    
    # segment a document by average size of segments
    def learn(self, data, num_segs=4):

        documents = data['documents']
#        if hasattr(data, 'documents'):
#            documents = data['documents']
#        else:
#            documents = data
            
        self.avg_seg_size = [0.0] * num_segs
        self.avg_seg_ratio = [0.0] * num_segs
        self.avg_size = 0.0
        
        
        num_docs = len(documents)
        #cumulative sum of size of each segment type in the set of documents
        for doc in documents:
            #num_segs = len(doc['segments'])
            #doc_size = len(doc['text'])
            #for seg in doc['segments']:
            for i in range(num_segs):
                seg = doc['segments'][i]
                #self.avg[seg['label']] += len(seg['text']) / len(doc['text'])
                #average character size
                #self.avg_seg_size[i] += len(seg['text'])
                #average paragraph size
                self.avg_seg_size[i] += len(seg['paragraphs'])
                self.avg_size += len(seg['paragraphs'])
        #averaging
        for i in range(num_segs):
            self.avg_seg_size[i] /= num_docs 

        #averaging
        self.avg_size /= num_docs 
            
        #ratio
        for i in range(num_segs):
            self.avg_seg_ratio[i] = self.avg_seg_size[i] / self.avg_size
        
        #print(self.avg_size)
        #print(self.avg_seg_size)
        #print(self.avg_seg_ratio)
        
        
    # segment a document by average size of segments
    def _segment_paragraphs(self, paragraphs):
        if self.strategy == 'ratio':
            return self._segment_by_average_ratio(paragraphs)
        elif self.strategy == 'size':
            return self._segment_by_average_size()
        else:
            print('ERROR ON SIZE SEGMENTER DEFAULT STRATEGY. USING RATIO.')
            return self._segment_by_average_size()
        
    
    # segment a document by average size of segments
    def _segment_by_average_ratio(self, paragraphs):
    
        #paragraphs = splitParagraphs(doc_text)
        
        #initialize empty list of starting positions
        segment_breakpoints = [0] * num_segs

        l = len(paragraphs)
        p = 0
        #lower = doc_text.lower()
        for i in range(num_segs):
        #for key in self.avg:
            m = self.avg_seg_ratio[i]
            #m = self.avg[key]
            p += round(m*l)
            #pos.append(p)
            segment_breakpoints[i] = p
    
        #remove the last break (which is the end of the text)
        del segment_breakpoints[-1]
        
        return {'segment_breakpoints':segment_breakpoints, 'confidence':[1.0]*num_segs}


    # segment a document by average size of segments
    def _segment_by_average_size(self):
    
        segment_breakpoints = [round(s) for s in self.avg_seg_size]
        
        #remove the last break (which is the end of the text)
        del segment_breakpoints[-1]
        
        return {'segment_breakpoints':segment_breakpoints, 'confidence':[1.0]*num_segs}    