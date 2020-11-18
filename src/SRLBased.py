"""

Brandon Cuadrado - 109237297
CSE 628, Final Project

Generation of Reading Comprehension Questions

Implementation of Automatic Question Generation using the DeconStructure Algoirthm
as described in "Infusing NLU into Automatic Question Generation" [Mazidi, 2016]

"""

import spacy
from spacy.pipeline import DependencyParser
from nltk import Tree
from tabulate import tabulate
import os
import sys
import progressbar
from practnlptools.tools import Annotator
import json

nlp = spacy.load('en')
annotator =  Annotator()

class template:
    def __init__(self, questions):
        self.questions = questions

    def match(self, ph):
        
        for question in self.questions:
            quest_word_list = question[0].split(' ')
            output_question = ""
            for word in quest_word_list:
                if (self.match_word(word, ph) == ""):
                    return False

            answer_word_list = question[1].split(' ')
            output_answer = ""
            for word in answer_word_list:
                if (self.match_word(word, ph) == ""):
                    return False
        
        # All necessary deps and args are found
        return True

    def match_word(self, word, ph):
        # if not a variabe, just use the word
        if ((not word.startswith('{')) or \
                (not word.endswith('}'))):
                return word
                
        word = word[1:len(word) - 1]
        word = word.split(';')
        arg = word[0]
        dep = word[1]

        arg_list = arg.split('|')
        dep_list = dep.split('|')

        # Check for matching arg and dep
        match = False
        for entry in ph.entries:
            dep_match = False
            arg_match = False
            if entry.token:
                if '_any' in dep_list or entry.token.dep_ in dep_list:
                    dep_match = True

            if '_any' in arg_list or entry.arg in arg_list:
                arg_match = True

            if dep_match and arg_match:
                match = True
                break

        if (match):
            return entry.text
        else:
            return ""

    def get_questions(self,ph):
        output_questions = []

        # iterate through all questions for this template
        for question in self.questions:

            # match all words in the question
            quest_word_list = question[0].split(' ')
            output_question = ""
            for word in quest_word_list:
                output_question += self.match_word(word, ph) + " "

            output_question = output_question[:len(output_question)-1] + "?"

            # match all words in the answer
            answer_word_list = question[1].split(' ')
            output_answer = ""
            for word in answer_word_list:
                output_answer += self.match_word(word,ph) + " "

            output_answer = output_answer[:len(output_answer)-1]
            
            output_questions.append((output_question, output_answer))

        return output_questions            

class phrase_entry:
    def __init__(self, const, text, arg, head, gov, token):
        self.const = const
        self.text = text
        self.head = head
        self.gov = gov
        self.arg = arg
        self.token = token

class phrase:

    # Phrases can match multiple
    templates = [\
        template([("What did {_any;nsubj} {V;_any} ", "{A1;dobj}")]),
        template([("What {V;_any} {A1;_any}", "{A0;_any}")]),
        template([("When did {A0;nsubj} {V;_any}", "{AM-TMV;_any}")]),
        template([("What {AM-MOD;aux} {A0;nsubj} do", "{V;_any}")]),
        template([("Why do {A0;nsubj} {V;_any}", "{AM-VNC;_any}")]),
        template([("Why {V;_any} {A1;nsubj} {A1;acomp}", "{AM-VNC;_any}")]),
        template([("Where does {A0;nsubj} {V;_any}", "{AM-LOC;_any}")]),
        template([("What does {A0;nsubj} {V;_any}", "{A1;dobj}")]),
        template([("How do {_any;nsubj} {V;_any} {_any;dobj}", "{AM-MNR;advmod|}")]),
        template([("Why does {A0;nsubj} {V;_any}", "{AM-CAU;prep|_any}")]),
        template([("Why {V;_any} {A1;nsubj} {A1;acomp}", "{AM-CAU;prep|_any}")]),
        template([("What {V;_any} {_any;nsubj} {_any;prep}", "{_any;pobj}")]),
        template([("What {V;_any} {A1;nsubj}", "{A1;acomp}")]),
        template([("What {V;_any} {_any;nsubj} {_any;conj} {_any;prep}", "{_any;pobj}")])]

    def __init__(self, entries):
        self.entries = entries

    def print_phrase(self):
        iterable_entries = self.entries_iter()

        print tabulate(iterable_entries, headers=['constituent', 'text', 'arg', 'head', 'gov', 'token'])


    def entries_iter(self):
        iter = []
        for e in self.entries:
            it = []
            it.append(e.const)
            it.append(e.text)
            it.append(e.arg)
            if e.token:
                it.append(e.head.text)
                it.append(e.gov)
                it.append(e.token.dep_)
            else:
                it.append("")
                it.append("")
                it.append("")

            iter.append(it)

        return iter

    def classify(self):
        temp_indices = []
        for i in range(len(self.templates)):
            t = self.templates[i]

            # return first found match
            if (t.match(self)):
                temp_indices.append(i);

        # no match found
        return temp_indices;

    def get_questions(self):
        temp_indices = self.classify()

        if len(temp_indices) <= 0:
            return []

        else:
            questions = []
            for i in temp_indices:
                temp = self.templates[i]

                questions.extend(temp.get_questions(self))

            return questions

class pattern:

    constituents = {
        "A0"        :   "agent"     ,
        "A1"        :   "patient"   ,
        "A2"        :   "patient"   ,
        "A3"        :   "patient"   ,
        "A4"        :   "patient"   ,
        "A5"        :   "patient"   ,
        "AM-ADV"    :   "general-purpose" ,
        "AM-CAU"    :   "cause"     ,
        "AM-DIR"    :   "direction" ,
        "AM-DIS"    :   "discourse marker" ,
        "AM-EXT"    :   "extent"    ,
        "AM-LOC"    :   "location"  ,
        "AM-MNR"    :   "manner"    ,
        "AM-MOD"    :   "modal verb"  ,
        "AM-NEG"    :   "negation marker" ,
        "AM-PNC"    :   "purpose"   ,
        "AM-PRD"    :   "predication" ,
        "AM-REC"    :   "reciprocal" ,
        "AM-TMP"    :   "temporal"  ,
        "V"         :   "verb"

    }

    def __init__(self, sent):
        self.sent = sent

        srl = annotator.getAnnotations(self.sent.text)['srl']
        self.srl = srl

        self.phrases = self.parse_srl(srl)

    def get_phrase_entries(self, parse=''):

        phrase_entries = []
        
        text = ""
        head = None
        gov = -1
        arg = ""
        token = None

        for i in range (len(parse)):
            entry = parse.items()[i]

            arg = entry[0]
            text = entry[1]

            words = text.split(' ')

            for tok in self.sent:
                if tok.text == words[0]:
                    token = tok
                    break

            if token:
                head = token.head
                gov = token.head.i

                
            # Use arg to get constituent
            if (arg.startswith('R-') or arg.startswith('C-')):
                arg_key = arg[2:].encode('utf-8')
            else:
                arg_key = arg.encode('utf8')

            if arg_key in self.constituents:
                const = self.constituents[arg_key]

            if (arg.startswith('R-')):
                const = "reference" + const
            if (arg.startswith('C-')):
                const = "continuation" + const
                    
            pe = phrase_entry(const, text, arg, head, gov, token)
            phrase_entries.append(pe)
           
        return phrase_entries

    def parse_srl(self, srl):

        phrases = []

        if srl == None:
            return None

        for parse in srl:        
            entries = self.get_phrase_entries(parse)

            p = phrase(entries)
            phrases.append(p)
            
        return phrases


def spacy_to_tree(node):
    if node.n_lefts + node.n_rights > 0:
        return Tree(node.orth_, [spacy_to_tree(child) for child in node.children])
    else:
        return node.orth_


def dependency_parse(sents):
    parser = DependencyParser(nlp.vocab)

    parsed_sents = []

    for sent in sents:
        parsed_sents.append(spacy_to_tree(sent.root).pretty_print())

    return parsed_sents

def generate_questions(text, passage_index, show_phrases = False):
    # Get simple pattern

    text = unicode(text, "utf-8")
    doc = nlp(text)
    questions = []

    for j, sent in enumerate(doc.sents):
        p = pattern(sent=sent)

        if show_phrases:
            print "Sentence:\t" + p.sent.text
            print "\n"

        if p.phrases == None:
            continue

        for ph in p.phrases:
            
            if (show_phrases):
                print 'Phrase:'
                ph.print_phrase()
                print '\n'
            
            ques = ph.get_questions()
            
            for q in ques:
                if len(q) == 0:
                    continue
                questions.append((q[0], q[1], passage_index, j))

    return questions


if __name__ == "__main__":
    writeOutputFile = True
    outputDir = os.path.dirname(__file__)
    numPassages = 500

    # Get CL arguments
    for ai, a in enumerate(sys.argv):
        if "-numPass" == a:
            numPassages = int(sys.argv[ai+1])    

    # Datasets to process
    dataFilenames = ["../data/the-legal-environment-and-business-law-v1.0-a.txt",
        "../data/public-speaking-practice-and-ethics.txt",
        "../data/social-psychology-principles.txt"]
    
    # Process data files, constructing questions for each passage
    textbooks = []
    for dataFilename in dataFilenames:
        passages = []
        dataFilePath = os.path.join(outputDir, dataFilename)
        dataFile = open(dataFilePath)
        for line in dataFile:
            if len(passages) > numPassages:
                break
            passageText = line.strip()
            if passageText != "":
                passages.append(passageText)
        textbooks.append(passages)
        dataFile.close()

    # Get questions by passage
    textbook_questions = []
    for i in range(len(textbooks)):
        
        print "Parsing " + dataFilenames[i]
        textbook_questions.append([])
        #for j in progressbar.progressbar(range(len(textbooks[i]))):
        for j in range(len(textbooks[i])):
            pass_questions = generate_questions(textbooks[i][j], j, False)
            if len(pass_questions) == 0:
                continue
            textbook_questions[i].extend(pass_questions)
    
    """
    print '---------------\n\nQuestions:\n'
    for question in questions:
        print question[0] + " " + question[1]
    """

    for i in range(len(textbooks)):
        outputFilename = dataFilenames[i].replace(".txt", "_questions_srl.txt")
        outputFilepath = os.path.join(outputDir, outputFilename)
        outputFile = open(outputFilepath, 'w')

        for question in textbook_questions[i]:
            quesDict = [{"qText"         :   question[0],
                        "aText"         :   question[1],
                        "passageIdx"    :   question[2],
                        "sentenceIdx"   :   question[3]
                        }]
            outputFile.write(json.dumps(quesDict) + "\n")

        outputFile.close()

        print "Questions written to file: " + outputFilepath



    