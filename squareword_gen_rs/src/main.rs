/// Generate NxN squares of words, using two input files. 
/// This is an exercise in learning Rust. See the python version for the first impl.

use std::fs::read_to_string;
use std::collections::HashSet;
use log::{info, warn};

 
// Read in the two files, return the top N words from the scrabble file
fn get_working_words(freq_csv_file: String, scrabble_words_file: String, top_n: usize, word_len: usize)
  -> Vec<String>
{
    // TODO: Switch both read_to_string()'s to read one line at a time.
    let mut scrabble_set = HashSet::new();
    for word in read_to_string(scrabble_words_file)
        .unwrap()
        .lines()
        .map(|s|
            s.trim()
            .to_string()
            .to_lowercase()
        ) {
        if word.len() == word_len {
          scrabble_set.insert(word.to_string());
        }
    }
    info!("Found {} scrabble words", scrabble_set.len());

    let mut working_words = Vec::new();
    // Read freq_csv_file, take first column, canonicalize, and keep only if it's in the Scrabble set
    for word in read_to_string(freq_csv_file)
        .unwrap()
        .lines()
        .map(|s|
          s.split_once(',')
          .unwrap().0
          .trim()
          .to_string()
          .to_lowercase()) {
        if scrabble_set.contains(&word) {
           working_words.push(word.to_string());
           if working_words.len() == top_n {
              break;
           }
        }
    }
    info!("Picked top {} words from freq file. Here are some of the top/bottom ones",
     working_words.len());

    for w in &working_words[0..10] {
        info!("   {w}");
    }
    info!("...");
    for w in &working_words[working_words.len()-10..] {
        info!("   {w}");
    }

   working_words
}


// Trie class, so we can efficiently iterate over string postfixes
// I got this from https://dev.to/timclicks/two-trie-implementations-in-rust-ones-super-fast-2f3m
// but tried to recreate it from memory first.
use std::collections::HashMap;

#[derive(Default, Debug)]
pub struct TrieNode {
    is_last: bool,
    children: HashMap<char, TrieNode>
}

pub struct Trie {
  root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Trie {
            root: TrieNode::default(),
        }
    }

    fn add_word(&mut self, word: &str) {
        let mut node = &mut self.root;
        for c in word.chars() {
            node = node.children.entry(c).or_default();
        }
        node.is_last = true;
    }

    fn add_words(&mut self, words: &Vec<String>) {
        for w in words {
            self.add_word(w);
        }
    }
}

// This iterator generates suffixes of words based on starting at a TrieNode
// and a list of valid chars for the next row. It is recursive internally, and
// will lazy-initialize a list of sub-iterators on the first call to next().
struct WordsFromValidCharsIter<'a> {
    // Inputs
    // Trie node for this point in the word position
    word_trie_node: &'a TrieNode,

    // Character for this step in the iterator tree. It's either one char, 
    // or an empty string (for the start of word). Stored as a string. 
    prefix_char: String,

    // List of list of valid chars for each relative char position.
    valid_next_row_chars: &'a [Vec<char>],

    // State
    // This the recursive inner loop, which gets set in next().
    // It calls down the tree of iterators.  I'm not 100% sure I understand
    // the lifetime, since this captures a stack variable when created. (?)
    string_iter: Option<Box<dyn Iterator<Item = String> + 'a>>,

    done: bool,
}

impl WordsFromValidCharsIter<'_> {
    fn new<'a>(word_trie_node: &'a TrieNode, prefix_char: String, valid_next_row_chars: &'a [Vec<char>])
        -> WordsFromValidCharsIter<'a> {
        WordsFromValidCharsIter {
            word_trie_node,
            prefix_char,
            valid_next_row_chars,
            string_iter: None,
            done: false, 
        }
    }

    fn make_child_iters(&mut self) {
        let mut child_iters = Vec::new();
        // Create an iterator for each possible next character, and pass to it a list of
        // valid chars for the rest of the (shorter) word.
        for char_to_try in &self.valid_next_row_chars[0] {
            match self.word_trie_node.children.get(&char_to_try) {
                None => {
                    // No word down this part of the trie
                    info!("  G: %{char_to_try} not in trie");
                    continue
                }
                Some(this_node) => {
                    info!("M: Making iter for {char_to_try}");
                    let next_child = WordsFromValidCharsIter::new(this_node, char_to_try.to_string(), 
                        &self.valid_next_row_chars[1..]);
                    child_iters.push(next_child);
                }
            }
        }

        // The magic happens here. I hope. This should create an iterator that returns a String item type,
        // but internally recurses through a tree of iterators. And since they're lazying created,
        // it should only create the one string that's about to be returned at the top.
        self.string_iter = Some(Box::new(child_iters.into_iter().flatten()));
    }
}

impl Iterator for WordsFromValidCharsIter<'_> {
    type Item = String; 
    // 
    fn next(&mut self) -> Option<Self::Item> {
        if self.done {
            // This shouldn't be a warning since the is_last check uses it intentionally.
            info!("  G!: WordsFromValidCharsIter called while done");
            return None;
        }

        if self.word_trie_node.is_last {
            // We're marking the end of the word. Return our single char,
            // and next call we'll return none. It shoudn't be None at the end of word.
            info!("  G-L: Got to is_last. Returning '{}'", self.prefix_char);
            self.done = true;
            return Some(self.prefix_char.clone()); 
        }

        if self.string_iter.is_none() {
            // Lazy initialization
            self.make_child_iters();
        }
        
        // Recurse down through children.
        match self.string_iter.as_mut()?.next() {
            // Take whatever suffix our children iterators produce, and put
            // our char in front of it.
            Some(suffix) =>  {
                info!("  G: returning {} + {}", self.prefix_char, suffix);
                Some(self.prefix_char.clone() + &suffix)
            }
            None => {
                self.done = true;
                None
            },
        }
    }


}

// Test code
fn gen_first_row(trie: &Trie, working_words: &Vec<String>) {

    for start_word in working_words {
        info!("** Start word: {start_word}");

        // This single element entries exactly equal to this word
        let mut valid_next_row_chars = Vec::new();
        for c in start_word.chars() {
            valid_next_row_chars.push(vec![c]);
        }

        let row_iter = WordsFromValidCharsIter::new(&trie.root, "".to_string(), &valid_next_row_chars);
        info!("Iterating over row_iter...");
        for w in row_iter {
            info!("  Next word: {w}")
        }
    }
}

// TODO: Create squares



// Main, with arg parsing
use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// CSV file where the first row is words, sorted in most popular first
    #[arg(short, long, default_value = "../unigram_freq.csv")]
    freq_csv_file: String,

    /// Text file of valid words to use
    #[arg(short, long, default_value = "../scrabble_words.txt")]
    scrabble_words_file: String,

    /// Cutoff for N most popular words to use
    #[arg(short, long, default_value_t = 5000)]
    top_n: usize,

    /// Len of words to use
    #[arg(short, long, default_value_t = 5)]
    word_len: usize,

    /// Print only valid double squares
    #[arg(short, long, default_value_t = false)]
    double_squares_only: bool,

    // Verbosity of logging. 0=off, 2=info
    #[arg(short, long, default_value_t = 2)]
    verbosity: usize,
}


fn main() {
    let args = Args::parse();

    // Pulled from https://docs.rs/stderrlog/0.5.4/stderrlog/
    stderrlog::new()
        .module(module_path!())
        .verbosity(args.verbosity)
        .init()
        .unwrap();

    info!("I'll try to pick {} words from {}", args.top_n, args.scrabble_words_file);

    let working_words = get_working_words(
        args.freq_csv_file, args.scrabble_words_file, args.top_n, args.word_len);

    let mut trie = Trie::new();
    trie.add_words(&working_words);

    // Not making squares yet, todo.
    gen_first_row(&trie, &working_words)


}