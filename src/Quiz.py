import spacy
import nltk
#nltk.download('punkt')
import sent2vec
from sklearn import metrics as mets
import json
import sys


class Sentence:
    def __init__(self, sent):
        self.sent = sent

        #self.chains = getAllChains(sent)
        #syntacticDeps(sent.root)

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


def similarity(SimModel, ansSent, passSent):
    ans_emb = SimModel.embed_sentence(ansSent) 
    pass_emb = SimModel.embed_sentence(passSent) 

    c = mets.pairwise.cosine_similarity(ans_emb.reshape(1, -1), pass_emb.reshape(1, -1))
    sim = c[0][0]

    return sim


def grade_dep(SimModel, question, resp, answers, hintSent, wordMatches, ranks, scoreWords):
    gr = 0
    sim = 0.0
    keywords_score = 0.0
    containedIn = 0.0
    for k in range(len(answers)):
        sim = max(sim, similarity(SimModel, resp, answers[k]))
        numb_keywords = 0.0
        notInQuestion = 0.0
        for j in scoreWords[k]:
            if str(wordMatches[k][j]) not in str(question):
                notInQuestion += 1.0
                if str(wordMatches[k][j]) in str(resp):
                    numb_keywords += 1.0
        keywords_score = max(keywords_score, round(numb_keywords/(notInQuestion/len(answers)), 2))
        words = nltk.word_tokenize(str(resp))
        for word in words:
            if word.lower() in str(answers[k]).lower():
                containedIn = max(containedIn, (len(word) + 0.0) / (len(str(answers[k])) + 0.0))

    gr = sim*0.5 + keywords_score*0.2 + containedIn*0.7
    if containedIn == 1.0: gr = 1.0
    if gr > 1.0: gr = 1.0

    return gr


def grade_srl(SimModel, question, resp, answers, hintSent):
    gr = 0
    sim = 0.0
    containedIn = 0.0
    for k in range(len(answers)):
        sim = max(sim, similarity(SimModel, resp, answers[k]))
        words = nltk.word_tokenize(str(resp))
        for word in words:
            if word.lower() in str(answers[k]).lower():
                containedIn = max(containedIn, (len(word) + 0.0) / (len(str(answers[k])) + 0.0))

    gr = sim*0.8 + containedIn*0.8
    if containedIn == 1.0: gr = 1.0
    if gr > 1.0: gr = 1.0

    return gr


def main(argv):
    global SimModel
    
    # Get CL args
    DEP = True
    if len(sys.argv) == 2:  print('(Dependency selected by default.)')
    elif len(sys.argv) == 3:
        if sys.argv[2] == '-srl': DEP = False
        elif sys.argv[2] == '-dep': DEP = True
    else:   print('Wrong arguments! => Dependency selected by default.')

    docFilename = sys.argv[1]

    nlp = spacy.load('en')

    # Load questions from given file
    docFile = open(docFilename)
    print("Reading questions from " + docFilename)
    qList = []
    pids = dict()
    for line in docFile:
        qs = json.loads(line)
        qList.append(qs)
        pid = qs[0]["passageIdx"]
        if pid not in pids:
            pids[pid] = True
    maxPassageIdx = max(pids.keys())
    docFile.close()

    # Read passages so we can load text
    dataFilename = docFilename.replace("_questions_dep", "").replace("_questions_srl", "")
    dataFile = open(dataFilename)
    print("Reading passages from " + dataFilename)
    passages = []
    for line in dataFile:
        if len(passages) > maxPassageIdx:
            break
        passageText = line.strip()
        if passageText != "":
            passages.append(Passage(passageText, nlp))
    dataFile.close()

    # Start giving user quiz
    grades = []
    pass_numbs = range(len(passages))
    for k in range(len(qList)):
        curr_pass = int(qList[k][0]['passageIdx'])
        if curr_pass in pass_numbs:
            print('\n' + passages[curr_pass].text)
            pass_numbs.remove(curr_pass)
        numb_variants = len(qList[k])
        answers = []
        ranks = []
        wordMatches = []
        scoreWords = []
        for l in range(numb_variants):
            question = qList[k][l]['qText']
            answers.append(qList[k][l]['aText'])
            passageNo = int(qList[k][l]['passageIdx'])
            sentNo = int(qList[k][l]['sentenceIdx'])
            hintSent = str(passages[curr_pass].sentences[sentNo].sent)
            if DEP:
                wordMatches.append(qList[k][l]['wordMatches'])
                ranks.append(qList[k][l]['rank'])
                scoreWords.append(qList[k][l]['scoreWords'])
            if l == 0:
                print('\n' + str(k+1) + '. ' + question)
            if l == numb_variants - 1:
                inp = raw_input("\nYour answer is: ")
                if inp == '-h':
                    print('> Hint: '+ hintSent)
                    resp = raw_input("\nNow, your answer is: ")
                elif inp == '-q':
                    print('\nYour total is: ' + str(round(sum(grades), 2)) + ' / ' + str(len(grades)))
                    print('Thanks for taking the quizz!')
                    sys.exit()
                else:
                    resp = inp

                if DEP: grades.append(grade_dep(SimModel, question, resp, answers, hintSent, wordMatches, ranks, scoreWords))
                else: grades.append(grade_srl(SimModel, question, resp, answers, hintSent))
                print('\nGrade: ' + str(grades[k]))
                sys.stdout.write('> Possible answer(s): ')
                for t in range(numb_variants):
                    if t == 0:
                        sys.stdout.write(str(answers[t]))
                    else:
                        sys.stdout.write(', '+str(answers[t]))
                print("")
    print('\nYour total is: ' + str(round(sum(grades), 2)) + ' / ' + str(len(grades)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("You need to provide a question file!")
        sys.exit()

    print("Loading sent2vec model...")
    SimModel = sent2vec.Sent2vecModel()
    SimModel.load_model('torontobooks_unigrams.bin')

    while True:
        main(sys.argv[1:])
    