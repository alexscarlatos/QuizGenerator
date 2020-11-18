# Extra Resources
To run DepBased.py or SRLBased.py, you will need to install spacy, which can be installed with pip  
To run Quiz.py, you will need to install sent2vec: https://github.com/epfml/sent2vec  
The pre-trained model we used was the toronto books unigrams (https://drive.google.com/file/d/0B6VhzidiLvjSOWdGM0tOX1lUNEk/view), which should be placed in the src folder  

# Data
In the data folder we have included the source textbooks in data-readable format  
Also included are the generated questions for each textbook, for both methods  
These question files can be re-generated using DepBased.py and SRLBased.py  

# Question file format
Each line represents a single question within a json stringified structure  
There is a list of all possible forms this question can have (different answers, ranks)  
Each list entry is a dictionary with the question properties, notably `qText`, `aText`, `passageIdx`, and `sentenceIdx`  

# Running our code
## DepBased.py
This runs the Dependency-based Question Generation algorithm on the textbooks in the data folder  
All generated questions will be written to output files, one for each text book with the suffix "_questions_dep"

Options:  
`-pSents`: print all sentences  
`-pDeps`: print all dependency trees  
`-pChains`: print all generated chains  
`-pPats`: print all generated patterns  
`-pFreqs`: print all generated frequency tables (one for each passage)  
`-pQs`: print all generated questions at the end, along with their ranks  
`-pQuiz`: print a sample quiz from a random passage  
`-numPass num_pasages`: specify number of passages to process from each textbook, default is 500  

## SRLBased.py
This runs the SRL-based Question Generation algorithm on the textbooks in the data folder  
All generated questions will be written to output files, one for each text book with the suffix "_questions_srl"

Options:  
`-numPass num_pasages`: specify number of passages to process from each textbook, default is 500

## Quiz.py
This will generate a quiz

Arguments:  
`question_file`: the path to the file that contains the quiz questions (file types that are exported by DepBased.py and SRLBased.py)

Options:  
[`-dep`, `-srl`]: the type of question file given, will determine which set of questions is selected and how scoring is done (default choice is dep)

# Group Members
Alex Scarlatos  
Brandon Cuadrado  
Eugenia Soroka  
