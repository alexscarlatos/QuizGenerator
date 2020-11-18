import json
import os
import random
import sys
import spacy

from PatternGen import getAllChains, getAllPatterns
from QuestionGen import questionFromPattern
from QuestionRanking import rankQuestion, tableRelevances

# Represents a sentence, will construct all possible patterns
class Sentence:
    def __init__(self, sent):
        self.sent = sent

        if printSentences:
            print("\nSentence:")
            print(sent)

        if printDependencies:
            print("\nDependencies:")
            printDeps(sent.root)

        # Extract all chains from sentence
        self.chains = getAllChains(sent)

        # Print all generated chains
        if printChains:
            self.printChains()

        # Construct patterns from chains
        pattern_candidates = getAllPatterns(self.chains)

        # Get questions for each pattern
        self.patterns = []
        for pattern in pattern_candidates:
            questions = questionFromPattern(pattern)
            self.patterns.append((pattern, questions))

        # Print all generated patterns
        if printPatterns:
            self.printPatterns()

        # Get word match frequencies from all questions
        self.wordMatchFreqs = []
        for i in range(0,len(tableRelevances)):
            self.wordMatchFreqs.append(dict())
        for p in self.patterns:
            for q in p[1]:
                # Take indicated word from q[3] (score list) and add to ith frequency table
                for i, scoreIdx in enumerate(q[3]):
                    w = q[0][scoreIdx]
                    if w not in self.wordMatchFreqs[i]:
                        self.wordMatchFreqs[i][w] = 1
                    else:
                        self.wordMatchFreqs[i][w] += 1

    def printChains(self):
        print("\nChains:")
        for chain in self.chains:
            print(chain)

    def printPatterns(self):
        print("\nPatterns:")
        for pattern in self.patterns:
            print(pattern[0])
            if printQuestions and len(pattern[1]) > 0:
                print(pattern[1])

# Represents a paragraph from the text source
class Passage:
    def __init__(self, text, nlp):
        self.text = text
        
        # Process each sentence
        info = nlp(unicode(text))
        self.sentences = []
        for sent in info.sents:
            # Generate Sentence object from spacy info
            sentence = Sentence(sent)
            self.sentences.append(sentence)

        # Get frequencies of important words at each sentence position for each sentence in this passage
        self.wordFreqs = []
        for i in range(0,len(tableRelevances)):
            self.wordFreqs.append(dict())
        for sent in self.sentences:
            for i, wm in enumerate(sent.wordMatchFreqs):
                for w in wm.keys():
                    if w not in self.wordFreqs[i]:
                        self.wordFreqs[i][w] = 1
                    else:
                        self.wordFreqs[i][w] += 1

        # Print word frequency tables
        if printFrequencyTables:
            print("\nFrequency Tables:")
            for wf in self.wordFreqs:
                print(wf)
    
    def printSentencePatterns(self):
        for sent in self.sentences:
            sent.printPatterns()

# recursively print a dependency tree
def printDeps(root):
    for child in root.children:
        print(str(root) + " " + str(root.pos_) + " ->" + str(child) + " " + child.dep_)
        printDeps(child)

if __name__ == "__main__":
    printSentences = False
    printDependencies = False
    printChains = False
    printPatterns = False
    printQuestions = True
    printFrequencyTables = False
    printFinalQuestions = False
    printSampleQuiz = False
    writeOutputFile = True
    outputDir = os.path.dirname(__file__)
    numPassages = 500

    # Get CL arguments
    for ai, a in enumerate(sys.argv):
        if "-pSents" == a:
            printSentences = True
        if "-pDeps" == a:
            printDependencies = True
        if "-pChains" == a:
            printChains = True
        if "-pPats" == a:
            printPatterns = True
        if "-pFreqs" == a:
            printFrequencyTables = True
        if "-pQs" == a:
            printFinalQuestions = True
        if "-pQuiz" == a:
            printSampleQuiz = True
        if "-numPass" == a:
            numPassages = int(sys.argv[ai+1])

    # Load spacy parsing model
    nlp = spacy.load('en')

    # Datasets to process
    dataFilenames = ["../data/the-legal-environment-and-business-law-v1.0-a.txt",
        "../data/public-speaking-practice-and-ethics.txt",
        "../data/social-psychology-principles.txt"]

    # Process data files, constructing questions for each passage
    textbooks = []
    for dataFilename in dataFilenames:
        print("Loading passages in " + dataFilename + "...")
        passages = []
        dataFile = open(dataFilename)
        for line in dataFile:
            if len(passages) > numPassages:
                break
            passageText = line.strip()
            if passageText != "":
                passages.append(Passage(passageText, nlp))
        textbooks.append(passages)
        dataFile.close()

    # Rank questions in the passages
    minQRank = 1
    for ti in range(0,len(textbooks)):
        print("Generating general corpus for " + dataFilenames[ti] + "...")

        if writeOutputFile:
            outputFilename = outputDir + dataFilenames[ti].replace(".txt", "_questions_dep.txt")
            outputFile = open(outputFilename, "w")
            print("Writing to " + outputFilename)

        # Cross-passage frequency table
        generalCorpus = []
        for i in range(0,len(tableRelevances)):
            generalCorpus.append(dict())

        # Total size of each frequency table, needed for Chi-Square
        totalWordCount = [0] * len(tableRelevances)

        # Generate frequency table across all textbooks that are not the current one
        for tii in range(0,len(textbooks)):
            if tii == ti:
                continue
            for p in textbooks[tii]:
                for i, wf in enumerate(p.wordFreqs):
                    for w, freq in wf.items():
                        if w not in generalCorpus[i]:
                            generalCorpus[i][w] = freq
                        else:
                            generalCorpus[i][w] += freq
                        totalWordCount[i] += freq

        # Go through every passage in the textbook
        allQRanks = []
        passageQuestions = []
        maxRank = 0
        for pi, passage in enumerate(textbooks[ti]):
            qDictForPassage = dict()
            for si, sentence in enumerate(passage.sentences):
                for pattern, questions in sentence.patterns:
                    for q in questions:
                        # Rank question, only keep if it ranks high enough
                        uniqueness, rank = rankQuestion(q[0], q[3], passage, generalCorpus, totalWordCount)
                        if rank > maxRank:
                            maxRank = rank

                        qaText = q[1] + " -> " + q[2]
                        
                        if printFinalQuestions:
                            allQRanks.append((qaText, rank))

                        # Package question info
                        entry = dict()
                        entry["qText"] = q[1]
                        entry["aText"] = q[2]
                        entry["wordMatches"] = q[0]
                        entry["scoreWords"] = q[3]
                        entry["rank"] = rank
                        entry["passageIdx"] = pi
                        entry["sentenceIdx"] = si

                        # Group together questions with the same qText
                        if q[1] not in qDictForPassage:
                            qDictForPassage[q[1]] = [entry]
                        else:
                            qDictForPassage[q[1]].append(entry)

            passageQuestions.append(qDictForPassage)

        # Normalize question ranks and save to file
        for qDict in passageQuestions:
            for qPoss in qDict.values():
                for q in qPoss:
                    q["rank"] /= maxRank
                if writeOutputFile:
                    outputFile.write(json.dumps(qPoss) + "\n")
        if writeOutputFile:
            outputFile.close()

        if printFinalQuestions:
            print("\nQuestion Rankings:")
            allQRanks.sort(key=lambda x: x[1])
            for q in allQRanks:
                print("{0} ({1})".format(*q))

        # Generate a quiz
        if printSampleQuiz:
            nonEmptyPassages = [pi for pi in range(0,len(passageQuestions)) if len(passageQuestions[pi]) > 1]
            if len(nonEmptyPassages) == 0:
                print("No sufficient passages to create a quiz with!")
            else:
                targetPassage = nonEmptyPassages[random.randint(0, len(nonEmptyPassages)-1)]
                print("\nQUIZ:")
                print("\n" + textbooks[0][targetPassage].text)
                for qPoss in passageQuestions[targetPassage].values():
                    for q in qPoss:
                        print("{0} -> {1}\n".format(q["qText"], q["aText"]))
