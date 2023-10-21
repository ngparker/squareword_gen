# squareword_gen
This is a set of experimenal algorithms to generate valid
NxN squares of words, where both columns and row are words
from a given dictionary.

It was inspired by squareword.com, and an algorithm from Annalee Flower Horne.

## TODO
* Get a better word-frequency list. This one seems to lean very heavily towards
words seen online, rather than in books.
* Filter out transpose-identical squares,  and squares with dup words.


## Attribution:
 *  `unigram_freq.txt`: from https://www.kaggle.com/datasets/rtatman/english-word-frequency/
 *  `scrabble_words.txt`: is from https://raw.githubusercontent.com/redbo/scrabble/master/dictionary.txt
