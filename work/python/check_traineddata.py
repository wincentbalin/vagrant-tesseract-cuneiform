#!/usr/bin/env python
"""This utility checks the error rate of Tesseract OCR traineddata."""

import os
import sys
import random
import logging
import textwrap
import argparse
import subprocess
import statistics
from abc import ABCMeta, abstractmethod
from datetime import datetime


def levenshtein(s: str, t: str) -> int:
    """Levenshtein distance algorithm, implementation by Sten Helmquist.
    Copied from https://davejingtian.org/2015/05/02/python-levenshtein-distance-choose-python-package-wisely/"""
    # degenerate cases
    if s == t:
        return 0
    if len(s) == 0:
        return len(t)
    if len(t) == 0:
        return len(s)

    # create two work vectors of integer distances
    v0 = []
    v1 = []

    # initialize v0 (the previous row of distances)
    # this row is A[0][i]: edit distance for an empty s
    # the distance is just the number of characters to delete from t
    for i in range(len(t)+1):
        v0.append(i)
        v1.append(0)

    for i in range(len(s)):
        # calculate v1 (current row distances) from the previous row v0
        # first element of v1 is A[i+1][0]
        # edit distance is delete (i+1) chars from s to match empty t
        v1[0] = i + 1

        # use formula to fill in the rest of the row
        for j in range(len(t)):
            cost = 0 if s[i] == t[j] else 1
            v1[j + 1] = min(v1[j]+1, v0[j+1]+1, v0[j]+cost)

        # copy v1 (current row) to v0 (previous row) for next iteration
        for j in range(len(t)+1):
            v0[j] = v1[j]

    return v1[len(t)]


def wer(ref: str, hyp: str) -> float:
    """Implemented after https://martin-thoma.com/word-error-rate-calculation/, but without numpy"""
    r, h = ref.split(), hyp.split()
    # initialisation
    d = [[0 for inner in range(len(h)+1)] for outer in range(len(r)+1)]
    for i in range(len(r)+1):
        d.append([])
        for j in range(len(h)+1):
            if i == j:
                d[0][j] = j
            elif j == 0:
                d[i][0] = i
    # computation
    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion    = d[i][j-1] + 1
                deletion     = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
    return d[len(r)][len(h)] / float(len(r))


class AbstractReport(metaclass=ABCMeta):
    @abstractmethod
    def add_test(self, reference: str, hypothesis: str):
        pass

    @abstractmethod
    def export_report(self):
        pass


class StatisticalWERReport(AbstractReport):
    """Just save string pairs and calculate mean WER and standard deviation as well."""
    def __init__(self):
        self.wer_list = []

    def add_test(self, reference: str, hypothesis: str):
        self.wer_list.append(wer(reference, hypothesis))

    def export_report(self):
        print('WER: mean {}, stdev {}'.format(statistics.mean(self.wer_list), statistics.stdev(self.wer_list)))


class HTMLTableReport(AbstractReport):
    """Put all tests into a HTML table and show errant ones."""
    def __init__(self):
        self.tests = []

    def add_test(self, reference: str, hypothesis: str):
        self.tests.append((reference, hypothesis))

    def export_report(self):
        with open('report.html', 'w', encoding='utf-8') as htmlfile:
            htmlfile.write('''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="ie=edge">
<title>Tesseract recognition report</title>
<style>
tr.even {
    background-color: #ddd
}

tr.error > td {
    border: 1px solid crimson
}
</style>
</head>
<body>
<h1>This is a Tesseract recognition report (created on ''' + datetime.now().isoformat() + ''')</h1>
<table>
<tr><th>Reference</th><th>Hypothesis</th></tr>
''')
            wer_list = []
            for row_index, (reference, hypothesis) in enumerate(self.tests, 1):
                wer_value = wer(reference, hypothesis)
                wer_list.append(wer_value)
                row_class = 'even' if row_index % 2 == 0 else 'odd'
                error_class = ' error' if wer_value > 0.0 else ''
                htmlfile.write('<tr class="{}{}"><td>{}</td><td>{}</td></tr>\n'.format(row_class, error_class, reference, hypothesis))
            htmlfile.write('</table>\n')
            htmlfile.write('WER: mean {}, stdev {}\n'.format(statistics.mean(wer_list), statistics.stdev(wer_list)))
            htmlfile.write('''</body>
</html>
''')


class HTMLParagraphReport(AbstractReport):
    """Put all tests into HTML paragraphs, hypothesis under the reference, so you can compare word-by-word much easier."""
    def __init__(self):
        self.tests = []

    def add_test(self, reference: str, hypothesis: str):
        self.tests.append((reference, hypothesis))

    def export_report(self):
        with open('report.html', 'w', encoding='utf-8') as htmlfile:
            htmlfile.write('''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="ie=edge">
<title>Tesseract recognition report</title>
<style>
p.even {
    background-color: #ddd
}

p.error {
    border: 1px solid crimson
}
</style>
</head>
<body>
<h1>This is a Tesseract recognition report (created on ''' + datetime.now().isoformat() + ''')</h1>
''')
            wer_list = []
            for row_index, (reference, hypothesis) in enumerate(self.tests, 1):
                wer_value = wer(reference, hypothesis)
                wer_list.append(wer_value)
                row_class = 'even' if row_index % 2 == 0 else 'odd'
                error_class = ' error' if wer_value > 0.0 else ''
                htmlfile.write('<p class="{}{}">\n{}<br/>\n{}<br/>\n</p>\n'.format(row_class, error_class, reference, hypothesis))
            htmlfile.write('WER: mean {}, stdev {}\n'.format(statistics.mean(wer_list), statistics.stdev(wer_list)))
            htmlfile.write('''</body>
</html>
''')


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__,
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('-l', '--language', default='akk', help='ISO-632-3 language code')
    argparser.add_argument('-i', '--wordlist', help='File with words to build tests from')
    argparser.add_argument('-w', '--wrap', type=int, default=80, help='Specify max width of a text line')
    argparser.add_argument('-f', '--font', help='Font names (multiple names must be separated with comma')
    argparser.add_argument('-e', '--wpe', type=int, default=10, help='Words per example')
    argparser.add_argument('-t', '--tests', type=int, default=1000, help='Amount of tests')
    argparser.add_argument('-x', '--exposure', type=int, default=0, help='Exposure of the test image')
    argparser.add_argument('-p', '--path', help='Tesseract path')
    argparser.add_argument('-d', '--tessdata', help='Tessdata directory')
    argparser.add_argument('-r', '--report', choices=['stat', 'html', 'htmlp'], default='stat', help='Type of report')
    args = argparser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

    text2image_cmd = os.path.join(args.path, 'text2image') if args.path else 'text2image'
    tesseract_cmd = os.path.join(args.path, 'tesseract') if args.path else 'tesseract'
    with open(args.wordlist, 'r', encoding='utf-8') as wl:
        wordlist = [word.rstrip() for word in wl]
    fonts = args.font.split(',')
    if args.report == 'stat':
        report = StatisticalWERReport()
    elif args.report == 'html':
        report = HTMLTableReport()
    elif args.report == 'htmlp':
        report = HTMLParagraphReport()
    for i in range(args.tests):
        test_ref = ' '.join(random.sample(wordlist, args.wpe))
        outputbase = 'test{:04}'.format(i)
        testfn = outputbase + '.txt'
        imagefn = outputbase + '.tif'
        boxfn = outputbase + '.box'
        logging.info('Creating test image file...')
        with open(testfn, 'w', encoding='utf-8') as testtext:
            testtext.writelines([line + '\n' for line in textwrap.wrap(test_ref, args.wrap)])
        subprocess.run([text2image_cmd,
                        '--outputbase', outputbase,
                        '--font', random.choice(fonts),
                        '--exposure', str(args.exposure),
                        '--text', testfn])
        os.remove(boxfn)
        os.remove(testfn)
        logging.info('OCRing test image file')
        subprocess.run([tesseract_cmd,
                        '-l', args.language,
                        imagefn, outputbase])
        with open(testfn, 'r', encoding='utf-8') as recognisedtext:
            test_hyp = ' '.join([line.rstrip() for line in recognisedtext.readlines()])
        os.remove(imagefn)
        os.remove(testfn)
        # Add reference and hypothesis to report
        report.add_test(test_ref, test_hyp)
    # Export results
    report.export_report()


if __name__ == '__main__':
    main()
