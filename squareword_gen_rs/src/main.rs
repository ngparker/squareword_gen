/// Generate NxN squares of words, using two input files. 
/// This is an exercise in learning Rust. See the python version for the first impl.

use std::fs::read_to_string;
use std::collections::HashSet;
 
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
    println!("Found {} scrabble words", scrabble_set.len());

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
    println!("Picked top {} words from freq file. Here are some of the top/bottom ones",
     working_words.len());

    for w in &working_words[0..10] {
        println!("   {w}");
    }
    println!("...");
    for w in &working_words[working_words.len()-10..] {
        println!("   {w}");
    }

   working_words
}

use std::collections::HashMap;

// I got this from https://dev.to/timclicks/two-trie-implementations-in-rust-ones-super-fast-2f3m
// but tried to recreate it from memory first.
#[derive(Default, Debug)]
struct TrieNode {
    is_last: bool,
    children: HashMap<char, TrieNode>
}

pub struct Trie {
  root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        return Trie {
            root: TrieNode::default()
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
}


fn main() {
    let args = Args::parse();

    println!("I'll try to read {} words from {} ", args.top_n, args.scrabble_words_file);

    let working_words = get_working_words(
        args.freq_csv_file, args.scrabble_words_file, args.top_n, args.word_len);

    let mut trie = Trie::new();
    trie.add_words(&working_words);


}