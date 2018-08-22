#!/usr/bin/env python
"""Create langdata directory and files for a Cuneiform corpus"""

import os
import sys
import argparse
import shutil
import collections
import itertools
import operator


def create_wordstats(cnt: collections.Counter) -> list:
    return sorted(cnt.items(), key=operator.itemgetter(1), reverse=True)


def create_wordlist(cnt: collections.Counter) -> list:
    return [word for word, _ in create_wordstats(cnt)]


def create_freq_wordlist(cnt: collections.Counter, threshold=0.95) -> list:
    nthr = int(float(sum(cnt.values())) * threshold)
    n = 0
    freq_wordlist = []
    for item in create_wordstats(cnt):
        freq_wordlist.append(item)
        n += item[1]
        if n > nthr:
            break
    return freq_wordlist


def create_bigramlist(cnt: collections.Counter) -> list:
    return [item for item, _ in sorted(cnt.items(), key=operator.itemgetter(1), reverse=True)]


def write_file(filename: str, wordlist: list, columns=2):
    with open(filename, 'w', encoding='utf-8') as f:
        if columns == 1:
            for item in wordlist:
                f.write('{}\n'.format(item))
        elif columns == 2:
            for item in wordlist:
                f.write('{} {}\n'.format(item[0], item[1]))
        else:
            raise NotImplementedError('I know not how to output this amount of columns')


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    argparser.add_argument('-d', '--directory', help='Output langdata directory')
    argparser.add_argument('-i', '--input', help='Corpus file')
    argparser.add_argument('-l', '--language', help='Language of the corpus (ISO 639-3)')
    args = argparser.parse_args()
    # Create statistics
    wordcount = collections.Counter()
    wordbigramcount = collections.Counter()
    bigramcount = collections.Counter()
    unigramcount = collections.Counter()
    with open(args.input, encoding='utf-8') as f:
        for line in f.readlines():
            words = line.split()
            wordbigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
            bigrams = [word[i] + word[i+1] for word in words for i in range(len(word)-1) if len(word) > 1]
            unigrams = list(itertools.chain.from_iterable([list(word) for word in words]))
            wordcount.update(words)
            wordbigramcount.update(wordbigrams)
            bigramcount.update(bigrams)
            unigramcount.update(unigrams)
    # Store files
    shutil.copy2(args.input, os.path.join(args.directory, '{}.{}'.format(args.language, 'training_text')))
    write_file(os.path.join(args.directory, '{}.{}'.format(args.language, 'wordlist')), create_wordlist(wordcount), columns=1)
    write_file(os.path.join(args.directory, '{}.{}'.format(args.language, 'word.bigrams')), create_bigramlist(wordbigramcount))
    write_file(os.path.join(args.directory, '{}.{}'.format(args.language, 'training_text.bigram_freqs')), create_wordstats(bigramcount))
    write_file(os.path.join(args.directory, '{}.{}'.format(args.language, 'training_text.unigram_freqs')), create_wordstats(unigramcount))


if __name__ == '__main__':
    main()
