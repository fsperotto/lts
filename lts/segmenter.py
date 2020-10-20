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
  
        #initialize empty list of starting positions
        segment_breakpoints = []
        confidence = []

        #remember last position found
        #char_position = 0
        prev_paragraph_position = 0
        
        #for each break get the corresponding regex
        for lbl_idx, pattern in enumerate(self.regex_rules):
            
            #default starting value is the next paragraph
            next_paragraph_position = prev_paragraph_position+1
            next_paragraph_confidence = 0.0
            
            #for each paragraph
            for i in range(prev_paragraph_position+1, len(paragraphs)):
                #search for correspondence
                if pattern.search(paragraphs[i]) is not None:
                    #add the position to the list
                    next_paragraph_position = i
                    next_paragraph_confidence = 1.0
                    break
                
            segment_breakpoints.append(next_paragraph_position)
            confidence.append(next_paragraph_confidence)
            
            prev_paragraph_position = next_paragraph_position
                
        return segment_breakpoints, confidence
    
  
    