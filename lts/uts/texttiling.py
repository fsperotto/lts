# -*- coding: utf-8 -*-
# Based on nltk texttiling implementation with some modifications
import re
import math
import numpy as np
from collections import Counter
from copy import deepcopy
from .utils import *

class TextTiling:
    """
    Reference:
        "TextTiling: Segmenting Text into Multi-paragraph Subtopic Passages"
    """

    def __init__(self, window=5, tokenizer=EnglishTokenizer()):
        """
        window: int, window size for similarity computation
        tokenizer: an object with tokenize() method,
                   which takes a string as argument and return a sequence of tokens.
        """
        self.window = window
        self.tokenizer = tokenizer

    def segment(self, document):
        """
        document: list[str]
        return list[int],
            i-th element denotes whether exists a boundary right before paragraph i(0 indexed)
        """
        # ensure document is not empty and every element is an instance of str
        assert(len(document) > 0 and len([d for d in document if not isinstance(d, str)]) == 0)
        # step 1, do preprocessing
        n = len(document)
        self.window = max(min(self.window, n / 3), 1)
        cnts = [Counter(self.tokenizer.tokenize(document[i])) for i in range(n)]

        # step 2, calculate gap score
        gap_score = [0 for _ in range(n)]
        for i in range(n):
            sz = min(min(i + 1, n - i - 1), self.window)
            lcnt, rcnt = Counter(), Counter()
            for j in range(i - sz + 1, i + 1):
                lcnt += cnts[j]
            for j in range(i + 1, i + sz + 1):
                rcnt += cnts[j]
            gap_score[i] = cosine_sim(lcnt, rcnt)

        # step 3, calculate depth score
        depth_score = [0 for _ in range(n)]
        for i in range(n):
            if i < self.window or i + self.window >= n:
                continue
            ptr = i - 1
            while ptr >= 0 and gap_score[ptr] >= gap_score[ptr + 1]:
                ptr -= 1
            lval = gap_score[ptr + 1]
            ptr = i + 1
            while ptr < n and gap_score[ptr] >= gap_score[ptr - 1]:
                ptr += 1
            rval = gap_score[ptr - 1]
            depth_score[i] = lval + rval - 2 * gap_score[i]

        # step 4, smooth depth score with fixed window size 3
        smooth_dep_score = [0 for _ in range(n)]
        for i in range(n):
            if i - 1 < 0 or i + 1 >= n:
                smooth_dep_score[i] = depth_score[i]
            else:
                smooth_dep_score[i] = np.average(depth_score[(i - 1):(i + 2)])

        # step 5, determine boundaries
        boundaries = [0 for _ in range(n)]
        avg = np.average(smooth_dep_score)
        stdev = np.std(smooth_dep_score)
        cutoff = avg - stdev / 2.0

        depth_tuples = list(zip(smooth_dep_score, list(range(len(smooth_dep_score)))))
        depth_tuples.sort()
        depth_tuples.reverse()
        hp = [x for x in depth_tuples if (x[0] > cutoff)]
        for dt in hp:
            boundaries[dt[1]] = 1
            for i in range(dt[1] - 4, dt[1] + 4 + 1):
                if i != dt[1] and i >= 0 and i < n and boundaries[i] == 1:
                    boundaries[dt[1]] = 0
                    break
        return [1] + boundaries[:-1]
