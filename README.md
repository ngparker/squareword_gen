# squareword_gen
This is an experiment to try generatating valid NxN squares of words,
where both columns and row are words from a given dictionary.

It was inspired by the squareword.com game, and an algorithm from Annalee Flower Horne.

It outputs things like this:

```
WordSquare 17 from word 4252/5000: double-word-square, unique
  gnomes
  repent
  outage
  origin
  moment
  snares
```

## Usage

```
usage: squareword_gen.py [-h] [--freq_csv_file FREQ_CSV_FILE]
                         [--scrabble_words_file SCRABBLE_WORDS_FILE]
                         [--top_n TOP_N] [--word_len WORD_LEN]
                         [--double_squares_only] [--log_details]
                         [--just_benchmark]

optional arguments:
  -h, --help            show this help message and exit
  --freq_csv_file FREQ_CSV_FILE
                        CSV file where the first row is words, sorted in most
                        popular first
  --scrabble_words_file SCRABBLE_WORDS_FILE
                        Text file of valid words to use
  --top_n TOP_N         Cutoff for N most popular words to use
  --word_len WORD_LEN   Len of words to use
  --double_squares_only
                        Print only valid double squares
  --log_details
  --just_benchmark
```

## TODO

* Get a better word-frequency list. The one here seems to
lean very heavily towards words seen online, rather than in
books. The [Wiktionary:Frequency lists/English/TV and Movie Scripts
(2006)](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/English/TV_and_Movie_Scripts_(2006))
looks good, but I haven't found it in machine-readable
form. Another possibility is [Leipzig Corpora
Collection](https://wortschatz.uni-leipzig.de/en/download/).


## Attribution:
 *  `unigram_freq.txt`: from https://www.kaggle.com/datasets/rtatman/english-word-frequency/
 *  `scrabble_words.txt`: is from https://raw.githubusercontent.com/redbo/scrabble/master/dictionary.txt (https://github.com/redbo/scrabble)
