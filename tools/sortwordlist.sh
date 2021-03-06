#!/bin/sh
# See LICENSE file for copyright and license details.

usage='Usage: $0

Takes a wordlist in stdin, one word per line, and outputs words in
order of frequency.'

test $# -ne 0 && echo "$usage" && exit 1

export LC_ALL=C # ensure reproducable sorting

sort | uniq -c | sort -nr | awk '{print $2}'
