# How relevant each part of a question is to its relevance score
# [idx_verb, idx_subj, idx_obj/attr/etc., idx_extra_info (if applicable)]
tableRelevances = [.1, .5, .35, .05]

# How many time the word w appears in the ith frequency table of the passage
def freqInPass(w, i, passage):
    if len(passage.wordFreqs) > i and w in passage.wordFreqs[i]:
        return passage.wordFreqs[i][w]
    else:
        return 0

# The sum of all word freqs in the ith frequency table of the passage
def totalWordCount(passage, i):
    if len(passage.wordFreqs) > i:
        return sum(passage.wordFreqs[i].values())
    else:
        return 0

# Given matched words of a sentence, determine how unique it is, given passages for domain and general corpus
def rankQuestion(qWords, qScoreList, domainPassage, generalCorpus, totalCrossPassCount):
    # For each word in question, get significance relative to domain passage
    uniqueness = []

    # i is table index and wi is word index in question
    for i, wi in enumerate(qScoreList):
        w = qWords[wi]

        if w in generalCorpus[i]:
            wCrossPassCount = generalCorpus[i][w]
        else:
            wCrossPassCount = 0

        # Expected value is probability of word across all passages times size of domain passage
        domainTotalWordCount = totalWordCount(domainPassage, i)
        exp = (float(wCrossPassCount) / totalCrossPassCount[i]) * domainTotalWordCount

        # Get number of times seen in domain passage
        obs = freqInPass(w, i, domainPassage)

        # Chi-Square
        if exp == 0:
            chi2 = obs**2
        else:
            chi2 = (obs - exp)**2 / exp
        uniqueness.append(chi2)
    
    while len(uniqueness) < len(tableRelevances):
        uniqueness.append(0)

    score = sum(u * r for u, r in zip(uniqueness, tableRelevances))

    return uniqueness, score