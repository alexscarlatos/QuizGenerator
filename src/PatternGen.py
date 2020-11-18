unpermittedWords = ["this", "that", "who", "which"]

# Get all possible chains in a sentence
def getAllChains(sent):
    # Get possible chain from each sentence token
    chain_candidates = []
    for tok in sent:
        # For all candidate tokens, find chain to closest verb
        if (tok.ent_type_ != "" or tok.pos_ == "NOUN" or tok.pos_ == "ADJ") and str(tok) not in unpermittedWords:
            head = tok
            chain = []
            while head.pos_ != "VERB" and head != sent.root:
                chain.append((head, head.dep_.encode()))
                head = head.head
            chain.append((head, head.dep_.encode()))
            if len(chain) <= 10:
                chain_candidates.append(chain)
    
    # Remove chains that are subsets of longer ones
    final_chains = []
    for c1 in chain_candidates:
        # Check all other chains
        isSubsetChain = False
        for c2 in chain_candidates:
            if c1 == c2:
                continue
            
            # See if this chain runs longer than us and matches
            c1_p = len(c1) - 1
            c2_p = len(c2) - 1
            while c1_p >= 0 and c2_p >=0 and c1[c1_p] == c2[c2_p]:
                c1_p -= 1
                c2_p -= 1
            if c1_p < 0:
                isSubsetChain = True
                break
        
        # Add this chain if it was not a subset of anything
        if not isSubsetChain:
            final_chains.append(c1)
    
    return final_chains

# Get all possible patterns given all possible chains in a sentence
def getAllPatterns(chain_candidates):
    pattern_candidates = []
    for c1_i in range(len(chain_candidates)):
        for c2_i in range(c1_i + 1, len(chain_candidates)):
            # Get two candidate chains
            c1 = chain_candidates[c1_i]
            c2 = chain_candidates[c2_i]
            c1_p = len(c1) - 1
            c2_p = len(c2) - 1

            # Must be rooted at the same verb
            if c1[c1_p] != c2[c2_p]:
                continue

            # Resulting pattern will have stem and two branches
            pattern_stem = []
            pattern_lbranch = []
            pattern_rbranch = []
            pattern = [pattern_stem, pattern_lbranch, pattern_rbranch]

            # Move down chains until they diverge
            while c1[c1_p] == c2[c2_p]:
                pattern_stem.append(c1[c1_p])
                c1_p -= 1
                c2_p -= 1

            # We don't want this pattern if one chain is a subset of the other
            if c1_p < 0 or c2_p < 0:
                continue

            # Add remaining tokens in c1
            while c1_p >= 0:
                pattern_lbranch.append(c1[c1_p])
                c1_p -= 1

            # Add remaining tokens in c2
            while c2_p >= 0:
                pattern_rbranch.append(c2[c2_p])
                c2_p -= 1

            pattern_candidates.append(pattern)
    return pattern_candidates