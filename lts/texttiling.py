###############################################################################
# TEXT TILING
###############################################################################


class TextTilingSegmenter(TextTilingTokenizer):
    
    
    # class variables
    #---------------

    ###############################################################################
    

    #constructor
    def __init__(self, w=200, k=5):

        #call super class constructor
        TextTilingTokenizer.__init__(self, w, k, stopwords=nltkstop.words(LANG), demo_mode=True)
        #w is the block sise (in tokens) by default 200
        #k is the window slide (in tokens) by default 5

    ###############################################################################


    # class methods
    #---------------

    # segment a document using TEXT TILING
    def segment(self, doc_text, paragraph_breaks):
  
        #paragraphs = splitParagraphs(doc_text)
        
        #text_tiling uses dounle newlines as paragraph separator
        #text = re.sub('\n', '\n\n', doc_text)

        #instantiate text tiling object
        #tt = TextTilingTokenizer(w=self.pw, k=self.pk, stopwords=nltkstop.words(LANG))
        #tt = TextTilingTokenizer(w=self.pw, k=self.pk, stopwords=nltkstop.words(LANG), demo_mode=True)
        
        #segment the text using text tiling
        #paragraph_breaks, segmented_text, gap_scores, smooth_scores, depth_scores, segment_boundaries, normalized_boundaries = self.tokenize(doc_text)
        gap_scores, smooth_scores, depth_scores, segment_boundaries = self.tokenize(doc_text)
        
        #print(gap_scores)
        #print(smooth_scores)
        #print(depth_scores)
        #print(segment_boundaries)
        #print(normalized_boundaries)
        #print(paragraph_breaks)
        
        #plt.plot(range(len(depth_scores)), depth_scores)
        #plt.plot(range(len(segment_boundaries)), segment_boundaries, 'r^')
        #plt.show()

        #translate char count boundary position to paragraph position
        boundaries = [paragraph_breaks.index(b) for b in normalized_boundaries]
        
        #initialize empty list of starting positions
        segment_breakpoints = []
        confidence = []

        #first position is the beginning of the text        
        #pos.append(0)
        #conf.append(1.0)

        #header/facts break is the first boundary
        if len(boundaries) >= 1 :
            segment_breakpoints.append(boundaries[0])
            confidence.append(1.0)
        else:
            segment_breakpoints.append(1)
            confidence.append(0.0)
        
        #facts/reasons break is the deepest boundary
        if len(boundaries) >= 2 :
            segment_breakpoints.append(boundaries[1])
            confidence.append(1.0)
        else:
            segment_breakpoints.append(2)
            confidence.append(0.0)

        #reasons/decision break is the last boundary
        if len(boundaries) >= 3 :
            segment_breakpoints.append(boundaries[-1])
            confidence.append(1.0)
        else:
            segment_breakpoints.append(3)
            confidence.append(0.0)

        #last position is the end of the text        
        #segment_breakpoints.append(len(paragraph_breaks))
        #confidence.append(1.0)
        
        return {'segment_breakpoints':segment_breakpoints, 'confidence':confidence}
    
    
    
    ###############################################################################


    def tokenize(self, text, paragraph_breaks=None):
        """Return a tokenized copy of *text*, where each "token" represents
        a separate topic."""

        #PRE-PROCESSING
        
        lowercase_text = text.lower()
        text_length = len(lowercase_text)
        
        #FP:
        if paragraph_breaks is None:
            paragraph_breaks = self._mark_paragraph_breaks(text)
        num_paragraphs = len(paragraph_breaks)
        
        # Tokenization step starts here

        #FP: estimate a good window size
        #self.w = num_paragraphs
        #print(self.w)
        
        # Remove punctuation
        nopunct_text = "".join(
            c for c in lowercase_text if re.match("[a-z\-' \n\t]", c)
        )
        nopunct_par_breaks = self._mark_paragraph_breaks(nopunct_text)

        tokseqs = self._divide_to_tokensequences(nopunct_text)

        # The morphological stemming step mentioned in the TextTile
        # paper is not implemented.  A comment in the original C
        # implementation states that it offers no benefit to the
        # process. It might be interesting to test the existing
        # stemmers though.
        # words = _stem_words(words)

        # Filter stopwords
        for ts in tokseqs:
            ts.wrdindex_list = [
                wi for wi in ts.wrdindex_list if wi[0] not in self.stopwords
            ]

        token_table = self._create_token_table(tokseqs, nopunct_par_breaks)
        # End of the Tokenization step

        # Lexical score determination
        if self.similarity_method == BLOCK_COMPARISON:
            gap_scores = self._block_comparison(tokseqs, token_table)
        elif self.similarity_method == VOCABULARY_INTRODUCTION:
            raise NotImplementedError("Vocabulary introduction not implemented")
        else:
            raise ValueError(
                "Similarity method {} not recognized".format(self.similarity_method)
            )

        if self.smoothing_method == DEFAULT_SMOOTHING:
            smooth_scores = self._smooth_scores(gap_scores)
        else:
            raise ValueError(
                "Smoothing method {} not recognized".format(self.smoothing_method)
            )
        # End of Lexical score Determination

        # Boundary identification
        depth_scores = self._depth_scores(smooth_scores)
        segment_boundaries = self._identify_boundaries(depth_scores)

        normalized_boundaries = self._normalize_boundaries(
            text, segment_boundaries, paragraph_breaks
        )
        # End of Boundary Identification
        segmented_text = []
        prevb = 0

        for b in normalized_boundaries:
            if b == 0:
                continue
            segmented_text.append(text[prevb:b])
            prevb = b

        if prevb < text_length:  # append any text that may be remaining
            segmented_text.append(text[prevb:])

        if not segmented_text:
            segmented_text = [text]

        if self.demo_mode:
            return gap_scores, smooth_scores, depth_scores, segment_boundaries
        return segmented_text
    
    

    
    
    
    
    
        

        # Tokenization step starts here

        # Remove punctuation
        nopunct_text = ''.join(c for c in lowercase_text
                               if re.match("[a-z\-\' \n\t]", c))
        nopunct_par_breaks = self._mark_paragraph_breaks(nopunct_text)

        tokseqs = self._divide_to_tokensequences(nopunct_text)

        # The morphological stemming step mentioned in the TextTile
        # paper is not implemented.  A comment in the original C
        # implementation states that it offers no benefit to the
        # process. It might be interesting to test the existing
        # stemmers though.
        #words = _stem_words(words)

        # Filter stopwords
        for ts in tokseqs:
            ts.wrdindex_list = [wi for wi in ts.wrdindex_list
                                if wi[0] not in self.stopwords]

        token_table = self._create_token_table(tokseqs, nopunct_par_breaks)
        # End of the Tokenization step

        # Lexical score determination
        if self.similarity_method == BLOCK_COMPARISON:
            gap_scores = self._block_comparison(tokseqs, token_table)
        elif self.similarity_method == VOCABULARY_INTRODUCTION:
            raise NotImplementedError("Vocabulary introduction not implemented")
        else:
            raise ValueError("Similarity method {} not recognized".format(self.similarity_method))

        if self.smoothing_method == DEFAULT_SMOOTHING:
            smooth_scores = self._smooth_scores(gap_scores)
        else:
            raise ValueError("Smoothing method {} not recognized".format(self.smoothing_method))
        # End of Lexical score Determination

        # Boundary identification
        depth_scores = self._depth_scores(smooth_scores)
        segment_boundaries = self._identify_boundaries(depth_scores)

        #print(len(segment_boundaries))

        normalized_boundaries = self._normalize_boundaries(text,
                                                           segment_boundaries,
                                                           paragraph_breaks)
        #print(len(normalized_boundaries))

        # End of Boundary Identification
        segmented_text = []
        prevb = 0

        for b in normalized_boundaries:
            if b == 0:
                continue
            segmented_text.append(text[prevb:b])
            prevb = b

        if prevb < text_length:  # append any text that may be remaining
            segmented_text.append(text[prevb:])

        if not segmented_text:
            segmented_text = [text]

        #MODIFYED RETURN
        #if self.demo_mode:
        #    return gap_scores, smooth_scores, depth_scores, segment_boundaries
        #return segmented_text
        return paragraph_breaks, segmented_text, gap_scores, smooth_scores, depth_scores, segment_boundaries, normalized_boundaries


    ###############################################################################

    #override text tiling paragraph marker
    def _mark_paragraph_breaks(self, text):
        
        pattern = re.compile('\n')
        matches = pattern.finditer(text)

        pbreaks = [pb.start() for pb in matches]
        
        #lstrip
        if pbreaks[0] == 0:
            del pbreaks[0]

        return pbreaks
