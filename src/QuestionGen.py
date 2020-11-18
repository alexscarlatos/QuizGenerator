# Maps pattern matching expression to output template, answer and score list
# Score list: [idx_verb, idx_subj, idx_obj/attr/etc., idx_extra_info (if applicable)]
question_templates = {
    "ROOT|ccomp|relcl;nsubj|nsubjpass;prep,pobj,*": ("{1} {0} {2} what?", "{4} {3}", [0,1,3,4]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;prep,pobj,*": ("{2} {1} {0} {3} what?", "{5} {4}", [0,1,4,5]),

    "ROOT|ccomp|relcl;nsubj|nsubjpass;conj,prep,pobj": ("{1} {0} {3} {4} what?", "{2}", [0,1,2,4]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;conj,prep,pobj": ("{2} {1} {0} {4} {5} what?", "{3}", [0,1,3,5]),

    "ROOT|ccomp|relcl;nsubj|nsubjpass;attr|dobj": ("{1} {0} what?", "{2}", [0,1,2]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;attr|dobj": ("{2} {1} {0} what?", "{3}", [0,1,3]),

    "ROOT|ccomp|relcl;nsubj|nsubjpass;attr|dobj,_any": ("{1} {0} what?", "{3} {2}", [0,1,2,3]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;attr|dobj,_any": ("{2} {1} {0} what?", "{4} {3}", [0,1,3,4]),

    #"ROOT|ccomp|relcl;nsubj|nsubjpass;attr|dobj,prep,*": ("What {0} {1} {3} {4}?", "{2}", [0,1,2,4]),
    #"ROOT|ccomp|relcl;nsubj|nsubjpass,_any;attr|dobj,prep,*": ("What {0} {2} {1} {4} {5}?", "{3}", [0,1,3,5]),
    
    "ROOT|ccomp|relcl;nsubj|nsubjpass;attr|dobj,prep,pobj,_any": ("{1} {0} {2} {3} what?", "{5} {4}", [0,1,2,4]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;attr|dobj,prep,pobj,_any": ("{2} {1} {0} {3} {4} what?", "{6} {5}", [0,1,3,5]),
   
    "ROOT|ccomp|relcl;nsubj|nsubjpass;attr|dobj,prep,pobj,prep,*": ("{1} {0} {2} {3} what?", "{4} {5} {6}", [0,1,2,4]),
    "ROOT|ccomp|relcl;nsubj|nsubjpass,_any;attr|dobj,prep,pobj,prep,*": ("{2} {1} {0} {3} {4} what?", "{5} {6} {7}", [0,1,3,5]),
}

# Match a template string to a pattern
def matchTemplateToPattern(template, pattern):
    matchedWords = []

    # Go through the template and try to match every word in the pattern
    p_i = 0
    for t_i, dep in enumerate(template):
        if p_i >= len(pattern):
            return None

        # * token means that we can match any number of words in the pattern
        if dep == "*":
            # Try to match remainder of the template at every point following this one in the pattern
            p_i_s = p_i
            while p_i_s <= len(pattern):
                sub_match = matchTemplateToPattern(template[t_i+1:], pattern[p_i_s:])

                # If we found a match
                if sub_match != None:
                    # Append skipped words as one word
                    matchedWords.append(" ".join([str(p[0]) for p in pattern[p_i:p_i_s]]))
                    # Append sub match and return
                    return matchedWords + sub_match
                else:
                    p_i_s += 1
            
            # If no matches were found then we failed
            return None
        # See if the current word matches the current token
        else:
            word = pattern[p_i]
            possDeps = dep.split("|")
            if dep != "_any" and word[1] not in possDeps:
                return None
            matchedWords.append(str(word[0]))
            p_i += 1
    
    # We need to match the whole pattern
    if p_i != len(pattern):
        return None

    return matchedWords

# Generate a question from the given pattern
# Returns list of results, each result is (list of matched words, question text, answer text)
def questionFromPattern(pattern):
    results = []
    for template, (questionPattern, answerPattern, scoreList) in question_templates.items():
        # Get stem and branches of template
        t_parts = template.split(";")

        # Try to match stem of template and pattern
        stemMatch = matchTemplateToPattern(t_parts[0].split(","), pattern[0])

        # Don't continue if stem didn't match
        if stemMatch is None:
            continue

        # Try both orderings of left and right branches
        matchedWords = []
        for lb, rb in [(pattern[1], pattern[2]), (pattern[2], pattern[1])]:
            lMatch = matchTemplateToPattern(t_parts[1].split(","), lb)
            rMatch = matchTemplateToPattern(t_parts[2].split(","), rb)

            # On success, build array of matched words
            if lMatch is not None and rMatch is not None:
                matchedWords = stemMatch + lMatch + rMatch
                break
        
        # Don't continue if branches didn't match
        if matchedWords == []:
            continue

        # Plug words into question and answer patterns
        question = questionPattern.format(*matchedWords)
        answer = answerPattern.format(*matchedWords)

        results.append((matchedWords, question, answer, scoreList))

    return results