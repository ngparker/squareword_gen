#!/usr/bin/python3
"""Generate NxN squares of words, like that would be used by https://squareword.org/
This is an experiment in how to generate them, and to see what words would show up
most commonly.

Nathan Parker
"""

import argparse
import csv
import random
import time


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


class WordTrie(dict):
    """ Datastructure holding a trie of words all the same length.

      This is stored as as a dict of single chars, each pointing to a trie,
      making up valid words.  The last char of a word has a value of "True"
      rather than another dict.  

      I tried another implementation that uses 26-element arrays in stead of
      dicts, but it's 3x slower for some reason (Python's dicts are fast).
    """

    def __init__(self, word_list):
        """
          Generate and store the trie.

          Args:
            word_list: list of strings N-chars long, used to generate the trie.
        """
        for word in word_list:
            # Start at the root for each word
            cur_trie = self

            # Create a dict for each node of the trie for all but the last letter
            # This traverses down the tree.
            for letter in word[:-1]:
                cur_trie = cur_trie.setdefault(letter, WordTrie([]))
            # The last leaf node is a "bool True" rather than an empty WordTrie.
            cur_trie.setdefault(word[-1], True)


def GenWordsFromValidChars(word_trie, valid_next_row_chars):
    """Return a generator that produces valid words.

      Args:
        word_trie: A node of a WordTrie, root or not.
        valid_next_row_chars: N-elem list of lists, with unique chars allowed at
           that position.
     Returns:
       Generator that produces valid words (strings)
    """
    # Iterate over all the chars in position zero, and see if they're
    # in the trie. If so, see if we can make a word.

    # depth = len(valid_next_row_chars)  # this is inverse depth, really
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
        word_trie: WordTrie, the root
        start_word: String of one word from the trie

      Returns:
        A generator that yields "squares," where a square is just a list
        of N words of length N.
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

      A valid square is a N words of length N that also form valid words
      in their vertical columns. This is called recursively, by setting
      coumn_trie_nodes for sub-calls.

      Args:
        word_trie: WordTrie, either node or root
        start_word: string of one word from the trie
        columne_trie_nodes: list of N nodes from the word-trie, corresponding to
          each char for the start_word
        log_prefix: Optional list of string to join+prefix output. We'll add start_word to it.

      Returns:
        Partial squares. It's a generator of list of words (rows) that make
        up part of the bottom of a square.
    """

    # New log obj with start_word added to the prefix.
    # This helps us figure out where we are in the process.
    next_log_prefix = log_prefix + [start_word]
    log = Logger('/'.join(next_log_prefix))

    log.log("Sub square start")
    # Last row?
    if column_trie_nodes[0] == True:
        yield []
        return

    # N lists of unique chars, taken from each of those nodes
    valid_next_row_chars = []

    # Compute valid_next_row_chars we'll iterate over.
    for this_node in column_trie_nodes:
        valid_next_row_chars.append(sorted(this_node.keys()))

    log.log("valid_next_row_chars = %s" % ('-'.join([''.join(charlist) for charlist in
            valid_next_row_chars])))

    # Look at all the valid words using the set of possible chars,
    # and see if there's a square that could be made from that word.
    for row_word_to_try in GenWordsFromValidChars(word_trie, valid_next_row_chars):
        log.log("  Trying %s" % row_word_to_try)

        # Get list of column trie nodes for this word
        next_column_trie_nodes = [column_trie_nodes[i].get(c) for i, c in
                                  enumerate(row_word_to_try)]

        # Recurse downward
        for sub_square in GenSubSquares(word_trie, row_word_to_try,
                                        next_column_trie_nodes, next_log_prefix):
            new_sub_square = [row_word_to_try] + sub_square
            log.log(" SS: yeilding [%s]" % (" / ".join(new_sub_square)))
            yield new_sub_square


def IsDoubleSquare(sq):
    """ Figure out if this has columns that differ from the rows.
    """

    for i, row_word in enumerate(sq):
        col_word = "".join([word[i] for word in sq])
        if col_word != row_word:
            return True

    return False


def WordsAreUnique(sq, is_double_square):
    """Figure out if there are any shared words in rows + cols.

    If not is_double_square, this'll look at just rows.
    """

    words = set()
    for i, row_word in enumerate(sq):
        if row_word in words:
            return False
        words.add(row_word)

        if is_double_square:
            col_word = "".join([word[i] for word in sq])
            if col_word in words:
                return False
            words.add(col_word)

    return True


def DoSomeBenchmarking(working_words, word_trie):
    """Print out some benchmarks at how fast we can make squares

      Args:
        working_words: list of words to use
        word_trie: root node of WordTrie
    """

    random.seed(123)
    random.shuffle(working_words)

    start_time = time.time()
    squares = 0
    pos = 0
    target_time = start_time + 10  # 10 seconds
    while time.time() < target_time:
        for sq in GenSquares(word_trie, working_words[pos]):
            squares += 1

        pos += 1
        if pos >= len(working_words):
            pos = 0

    dur = time.time() - start_time
    print("Ran %d squares in %.1f sec, or %.0f squares/sec" % (squares, dur,
          squares / dur))


def main():
    """ Main
    """

    parser = argparse.ArgumentParser()
    # Inputs
    parser.add_argument('--freq_csv_file', type=str,
                        default='unigram_freq.csv',
                        help="CSV file where the first row is words, "
                        "sorted in most popular first")
    parser.add_argument('--scrabble_words_file', type=str,
                        default='scrabble_words.txt',
                        help="Text file of valid words to use")

    # Knobs
    parser.add_argument('--top_n', type=int, default=5000,
                        help="Cutoff for N most popular words to use")
    parser.add_argument('--word_len', type=int, default=5,
                        help="Len of words to use")
    parser.add_argument('--double_squares_only', action="store_true",
                        help="Print only valid double squares")

    # Debugging options
    parser.add_argument('--log_details', action="store_true")
    parser.add_argument('--just_benchmark', action="store_true")

    args = parser.parse_args()
    LOG_DETAILS = args.log_details

    working_words = GetWorkingWords(args.freq_csv_file, args.scrabble_words_file,
                                    args.top_n, args.word_len)

    word_trie = WordTrie(working_words)

    if args.just_benchmark:
        DoSomeBenchmarking(working_words, word_trie)
        return

    # Example valid 6x6 square:
    #  market
    #  avenue
    #  relics
    #  knight
    #  euchre
    #  rested

    print("Generating Squares..\n")
    sq_num = 0
    for word_num, start_word in enumerate(working_words):
        for sq in GenSquares(word_trie, start_word):
            # Collect some classifications of this sq.
            is_double_square = IsDoubleSquare(sq)
            words_are_unique = WordsAreUnique(sq, is_double_square)
            if args.double_squares_only and (not is_double_square
                                             or not words_are_unique):
                continue
            desc = "WordSquare %d from word %d/%d: %s-word-square, %s" % (
                sq_num, word_num, len(working_words),
                "double" if is_double_square else "single",
                "unique" if words_are_unique else "non-unique")
            print(desc)
            for word in sq:
                print("  " + word)
            print("")
            sq_num += 1

    print("Made %d squares" % sq_num)


if __name__ == "__main__":
    main()
