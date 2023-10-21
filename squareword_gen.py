#!/usr/bin/python3
"""Generate NxN squares of words, like that would be used by https://squareword.org/
This is an experiment in how to generate them, and what words would show up
most commonly.

Nathan Parker
"""

import argparse
import csv
from itertools import product


LOG_DETAILS = False


class Logger:
    """A simple logger class that lets you set a prefix string.
    """

    def __init__(self, prefix_str):
        self._prefix_str = prefix_str

    def log(self, msg):
        if LOG_DETAILS:
            print(self._prefix_str + " " + msg)


def GetWorkingWords(freq_csv_file, scrabble_words_file, top_n, word_len):
    """Read in the two files, return the top N from the scrabble file

    Args:
      freq_csv_file: filename of csv file, w/ header, with [word, frequency_count]
      scrabble_words_file: filename of flat text file of scrabble words
      top_n: integer of how many words to return
      word_len: integer of word length to pick out
    """

    scrabble_set = set()
    with open(scrabble_words_file, 'r') as f:
        for line in f:
            scrabble_set.add(line.lower().strip())
    print("Found %d scrabble words" % (len(scrabble_set)))

    working_words = []
    with open(freq_csv_file, newline='') as csvfile:
        for row in csv.reader(csvfile, delimiter=','):
            # Assume it's sorted by frequency, so we just count the top N
            # that are scrabble words
            word = row[0].lower().strip()
            if (len(word) != word_len):
                continue
            if word in scrabble_set:
                working_words.append(word)
                if len(working_words) >= top_n:
                    break

    print("Picked the top %d scrabble words. Here's some of the top/bottom ones:" %
          (len(working_words)))

    for word in working_words[0:10]:
        print("  " + word)
    print("...")
    for word in working_words[-10:]:
        print("  " + word)

    print("")

    return working_words


def BuildWordTrie(working_words, word_len):
    """Build a trie and return it

      Args: 
        working_words: list of words all length word_len
        word_len: integer

      Returns:
        The trie, which is a dict of single chars, each pointing to a trie, making up valid words
        The last char of a word has a value of "True" rather than another dict.
     """

    root = dict()
    for word in working_words:
        # Start at the root for each word
        cur_dict = root

        # Create a dict for each node of the trie for all but the last letter
        for letter in word[:-1]:
            cur_dict = cur_dict.setdefault(letter, {})
        # We save some RAM (like 1/2 of it) by not putting an empty dict in
        # the leaf node. Just put the bool True.
        cur_dict.setdefault(word[-1], True)

    return root


def GenWordsFromValidChars(word_trie, valid_next_row_chars):
    """Return a generator that produces valid words.

      Args:
        word_trie: dict-trie of single chars making up valid words
        valid_next_row_chars: N-elem list of lists, with unique chars allowed at
           that position.
     Returns:
       Generator that produces valid words (strings)
    """

    # Iterate over all the chars in position zero, and see if they're
    # in the trie. If so, see if we can make a word.
    depth = len(valid_next_row_chars)  # this is inverse depth, really
    # print("  G: -- Called with %d positions left" % depth)
    for char_to_try in valid_next_row_chars[0]:
        if char_to_try not in word_trie:
            # No word down this part of the trie
            # print("  G%d: %s not in trie" % (depth, char_to_try))
            continue

        this_node = word_trie.get(char_to_try)

        # Check if it's a leaf node (they're == True rather than a dict)
        # Then this is the last char in the word.
        if this_node == True:
            # print("  G%d:   Yielding EOW %s" % (depth, char_to_try))
            yield char_to_try
            continue

        # print("  G%d: recusing down %s" % (depth, char_to_try))
        # Otherwise, recurse. If this call has no items,
        # then there's no valid suffix from here on, so we won't
        # use this char_to_try.
        for suffix in GenWordsFromValidChars(this_node, valid_next_row_chars[1:]):
            # print("  G%d:   Yielding %s + %s" % (depth, char_to_try, suffix))
            yield char_to_try + suffix
        # print("  G%d:  return" % depth)


def GenSquares(word_trie, start_word):
    """Generate all the squares that have start_word at the top.

      A valid square is a N words of length N that also form
      valid words in their vertical columns.

      Args:
        word_trie: dict-trie of single chars making up valid words
        start_word: string of one word from the trie

      Returns:
        list of "squares," where a square is just a list of N words of length N.
     """

    # This sets up this new square, and then we call GenSubSquares recursively.
    log = Logger(start_word)
    log.log("--- TOP START WORD ---")

    column_trie_nodes = []
    for c in start_word:
        # Look for possible vertical words
        if c not in word_trie:
            log.log(" --> NO MATCH FOR TOP START WORD %s of %s" %
                    (c, start_word))
            return
        column_trie_nodes.append(word_trie.get(c))

    for sq in GenSubSquares(word_trie, start_word, column_trie_nodes, []):
        yield [start_word] + sq


def GenSubSquares(word_trie, start_word, column_trie_nodes=[], log_prefix=[]):
    """Generate all the partial squares that have start_word at the top, recursively.

      A valid square is a N words of length N that also form
      valid words in their vertical columns. This is called recursively,
      by setting coumn_trie_nodes for sub-calls.

      Args:
        word_trie: dict-trie of single chars making up valid words
        start_word: string of one word from the trie
        columne_trie_nodes: list of N nodes from the word-trie, corresponding to
          each char for the start_word
        log_prefix: Optional list of string to join+prefix output. We'll add start_word to it.

      Returns:
        list of "squares," where a square is just a list of N words of length N.
        If called recursively, it'll return a list of M words, M<N.
    """

    # New log obj with start_word added to the prefix.
    # This helps us figure out where we are in the process.
    next_log_prefix = log_prefix + [start_word]
    log = Logger('/'.join(next_log_prefix))

    # Called recursively
    log.log("Sub start word")
    # Last row?
    if column_trie_nodes[0] == True:
        log.log("   EOS: END OF SQUARE")
        yield []
        return

    # N lists of unique chars, taken from each of those nodes
    valid_next_row_chars = []

    # Compute valid_next_row_chars we'll iterate over.
    for this_node in column_trie_nodes:
        valid_next_row_chars.append(sorted(this_node.keys()))

    log.log("valid_next_row_chars = %s" % ('-'.join([''.join(charlist) for charlist in
            valid_next_row_chars])))

    # We could enumerate all combinations of next-row-words and
    # check if they're real words, like...
    #  for w in product(*valid_next_row_chars):
    #     print(" word? " + ''.join(w))
    # But we can short-circuit that.

    for row_word_to_try in GenWordsFromValidChars(word_trie, valid_next_row_chars):
        log.log("  Trying %s" % row_word_to_try)

        # Get list of column trie nodes for this word
        next_column_trie_nodes = [column_trie_nodes[i].get(c) for i, c in
                                  enumerate(row_word_to_try)]

        # Recurse
        for sub_square in GenSubSquares(word_trie, row_word_to_try,
                                        next_column_trie_nodes, next_log_prefix):
            new_sub_square = [row_word_to_try] + sub_square
            log.log(" SS: yeilding [%s]" % (" / ".join(new_sub_square)))
            yield new_sub_square



def main():
    """ Main
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--freq_csv_file', type=str,
                        default='unigram_freq.csv')
    parser.add_argument('--scrabble_words_file', type=str,
                        default='scrabble_words.txt')

    parser.add_argument('--top_n', type=int, default=5000)
    parser.add_argument('--word_len', type=int, default=5)
    parser.add_argument('--log_details', action="store_true")

    args = parser.parse_args()

    global LOG_DETAILS
    LOG_DETAILS = args.log_details
    print("LOG_DETAILS = %d" % LOG_DETAILS)

    working_words = GetWorkingWords(args.freq_csv_file, args.scrabble_words_file,
                                    args.top_n, args.word_len)

    word_trie = BuildWordTrie(working_words, args.word_len)
    print("Generating Squares..\n")

    # Example valid square:
    #  snuff
    #  airer
    #  reata
    #  octet
    #  seeds
    # working_words = ["snuff"]

    squares = []
    for start_word in working_words:
        for sq in GenSquares(word_trie, start_word):
            for word in sq:
                print(word)
            print("")
            squares.append(sq)

    print("Made %d squares" % len(squares))


if __name__ == "__main__":
    main()
