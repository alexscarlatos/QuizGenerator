import os
from pyquery import PyQuery as pq
import re
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a folder with html files to parse!")
        exit()
    
    # Go through every html file in target directory, and write passages to output file
    dirName = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
    targetDir = os.listdir(dirName)
    outputFilename = dirName.split('/')[-2] + ".txt"
    print("Creating " + outputFilename)
    outputFile = open(outputFilename, "w")
    for targetFile in targetDir:
        if not targetFile.endswith(".html"):
            continue
        
        # Open file with pyquery parser
        filepath = dirName + targetFile
        d = pq(filename=filepath)

        # Text we care about has the "para" class
        passages = d(".para")
        for p in range(0, len(passages)):
            # Get passage text
            pText = passages.eq(p).text()
            if pText is None:
                continue

            # Remove unicode characters and convert to ascii
            if isinstance(pText, unicode):
                pText = re.sub(r'[^\x00-\x7F]+',' ', pText).encode()

            # Write text to output
            outputFile.write(pText + "\n")
        outputFile.write("\n")

    outputFile.close()
