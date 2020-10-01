####################
# GET DATA FUNCTIONS
####################

# xml labels
FAD_HEAD = 'headerCA'
FAD_FACT = 'faitsCA'
FAD_REAS = 'motifsCA'
FAD_CONC = 'conclusionCA'

IDX_HEAD = 0
IDX_FACT = 1
IDX_REAS = 2
IDX_CONC = 3

idx_to_lab = lambda idx: [FAD_HEAD, FAD_FACT, FAD_REAS, FAD_CONC][idx]
lab_to_idx = lambda lab: {FAD_HEAD:IDX_HEAD, FAD_FACT:IDX_FACT, FAD_REAS:IDX_REAS, FAD_CONC:IDX_CONC}[lab]    

# define language
LANG = 'french'

# constants
DATA_FILE = "data.pickle"
XML_FILTER = "*.xml"


def savePickle(data, filename, folder="", verbose=True):
    if verbose:
        print("Saving pickle file... ", end='')
    with open(folder + filename, 'wb') as fp:
        pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)            
    if verbose:
        print("[DONE]")

def loadPickle(filename, folder="", verbose=True):
    if verbose:
        print("Reading pickle file... ", end='')        
    #if a pickle file exists, read it
    if os.path.isfile(folder + filename):
        with open(folder + filename, 'rb') as fp:
            data = pickle.load(fp)
        if verbose:
            print("[DONE]")      
        return data
    else:
        if verbose:
            print("file not found.")      
        return None

        
def loadData(datapickefile, folder="", xmlfilefilter=None):
    
    #if a pickle file exists, read it
    data = loadPickle(datapickefile, folder=folder)

    #otherwise, read it from xml files
    if data is None:

        print(" |-Reading XML files... ", end='')        
        documents = extractFromXMLfolder(directory, xmlfilefilter)
        print("[DONE]")      
        
        print(" |-Preparing data... ", end='')
        segments = []
        for doc in documents:
            for segment in doc['segments']:
                segments.append(segment)
        #data['segments'] = [ (segment for segment in doc['segments']) for doc in documents]
        print("[DONE]")      
        
        print(" |-Making full vocabulary... ", end='')
        all_words = []
        for doc in documents:
            all_words.extend(splitWords(doc['text']))
        vocabulary = tokenize(all_words)
        print("[DONE]")      
        print(" |-Making segment vocabulary... ", end='')
        for segment in segments:
            segment['vocabulary'] = tokenize(splitWords(segment['text']))
        print("[DONE]")      
        print(" |-Making paragraph vocabulary... ", end='')
        for segment in segments:
            for parag in segment['paragraphs']:
                parag['vocabulary'] = tokenize(splitWords(parag['text']))
        print("[DONE]")      
        
        print(" |-Making BoW feature set description for segments... ", end='')       
        for segment in data['segments']:
            segment['bow_features'] = [voc in segment['vocabulary'] for voc in data['vocabulary']]
        print("[DONE]")      
        print(" |-Making BoW feature set description for paragraphs... ", end='')       
        for segment in segments:
            for parag in segment['paragraphs']:
                parag['bow_features'] = [voc in parag['vocabulary'] for voc in data['vocabulary']]
        print("[DONE]")      
        
        #print(" |-Formmating samples... ", end='')        
        #data['samples'] = [(segment['features'], segment['label']) for segment in data['segments']]
        #print("[DONE]")      
        
        #cat_words = []
        #for doc in documents:
        #    for segment in doc['segments']:
        #        cat_words[segment['label']].extend(segment['words'])

        #print(" |-Calculating word frequencies... ", end='')      
        #data['word_freq'] = FreqDist(data['words'])
        #print("[DONE]")      
        #
        #print(" |-Calculating vocabulary frequency... ", end='')    
        #data['voc_freq'] = FreqDist([word for word in data['words'] if word in data['vocabulary']])
        #print("[DONE]")      

        
        #data = {'documents':documents, 'segments':[], 'words':[], 'vocabulary':[], 'samples':[]} 
        #data = {'documents':documents, 'segments':segments, 'words':words, 'vocabulary':vocabulary} 

        data = {'documents':documents, 'segments':segments, 'vocabulary':vocabulary} 

        #savePickle(data, datapickefile, folder=folder)
        
    return data

###############################################################################


#Transform all the XML files into a single JSON file,
# but getting only the DIV elements
# as defined by FADILA
def extractFromXMLfolder(directory, filefilter):

    #initialize list of text docs and list of segments inside them
    documents = []

    #for each subdirectory in the base directory
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        #for each file corresponding to the filter
        for filename in fnmatch.filter(files, filefilter):
            
            #open the file
            inputfilepath = os.path.join(path, filename)
            with open(inputfilepath, "rt", encoding="UTF-8") as inputfile:
                
                print(filename + " ", end='')        

                #read raw data from file
                raw_data = inputfile.read()
                
                #remove unnecessary tags
                raw_data = re.sub(r'<.?type_arrêt>|<.?lieu_procès>|<.?date_procès>', '', raw_data)
                
                #convert raw data to xml structure
                xml_root = et.fromstring(raw_data)

                
                '''
                #search for segments (div tags)
                for elem in root.findall('div'):
                    #get segment text
                    segtext = elem.text
                    #eliminate spaces and new lines at the beginning
                    segtext = segtext.lstrip('\s\t\n\r')
                    #get segment category
                    segcat = elem.get('type')
                    #append to the list
                    doc['segments'].append({'text':segtext, 'label':segcat, 'filename':filename})
                '''

                #bits_of_text = root.xpath('//text()')

                #initialize list of segments
                segments = []
                
                #initialize list of starting positions (in char) for segments
                char_seg_breakpoints = []
                #initialize list of starting positions (in paragraphs) for segments
                paragraph_seg_breakpoints = []
                
                #initialize document full text (string)
                full_text = ""

                #initialize counter for paragraphs
                num_paragraphs = 0
                
                #the first segment (header) is not inside a div
                is_first_div = True
                
                #get back the plain text
                for xml_elem in xml_root.iter():
                    #get segment
                    #and eliminate spaces and new lines at the beginning
                    inner_text = sanitize(xml_elem.text)
                    #div marks a new segment
                    if xml_elem.tag == 'div':
                        #get break of the previous segment based on the actual size of the text
                        char_seg_breakpoints.append(len(full_text))
                        #first div separates header and facts
                        if is_first_div:
                            #previous text is header segment
                            #split in paragraphs
                            paragraphs = [{'text':parag} for parag in splitParagraphs(full_text)]
                            num_paragraphs += len(paragraphs)
                            paragraph_seg_breakpoints.append(num_paragraphs)
                            #prepare segment
                            segment = {'text':full_text, 'paragraphs':paragraphs, 'label':FAD_HEAD, 'filename':filename}
                            #append to the segments list
                            segments.append(segment)
                            #header segment done
                            is_first_div = False
                        #get next segment category
                        seg_cat = xml_elem.get('type')
                        #split in paragraphs
                        paragraphs = [{'text':parag} for parag in splitParagraphs(inner_text)]
                        num_paragraphs += len(paragraphs)
                        paragraph_seg_breakpoints.append(num_paragraphs)
                        #prepare segment
                        segment = {'text':inner_text, 'paragraphs':paragraphs, 'label':seg_cat, 'filename':filename}
                        #append to the segments list
                        segments.append(segment)
                    #complete the text
                    full_text += inner_text + '\n'
                #last break is the end of the file
                #char_seg_breakpoints.append(len(full_text))

                #remove last breakpoint (which is the end of the text)
                del paragraph_seg_breakpoints[-1]

                #initialize list of starting positions (in char) for paragraphs
                char_paragraph_breakpoints = [m.start() for m in re.finditer('\n', full_text)]
                
                #append header to the list
                #text = fulltext[:breaks[0]]
                #text = sanitize(text)
                #split in paragraphs
                #paragraphs = splitParagraphs(text)
                #segments.append({'text':text, 'paragraphs':paragraphs, 'label':'headerCA', 'filename':filename})

                with open(inputfilepath+'.txt', "wt", encoding="UTF-8") as outputfile:
                    outputfile.write(full_text)

                doc = {'filename':filename, 'text':full_text, 'paragraph_breakpoints':char_paragraph_breakpoints, 'segments':segments, 'segment_breakpoints':paragraph_seg_breakpoints}
                #doc = {'filename':filename, 'text':full_text, 'paragraph_breakpoints':char_paragraph_breakpoints, 'segments':segments, 'segment_breakpoints':paragraph_seg_breakpoints}

                #append to the list
                documents.append(doc)
                
    return documents
