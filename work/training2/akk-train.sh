#!/bin/sh
#
# Train Akkadian language
#export TEXT2IMAGE_EXTRA_ARGS="--leading 12"
export LEADING=12
./tesstrain.sh --lang akk --training_text corpus-12pt.txt --tessdata_dir /usr/share/tesseract-ocr/tessdata --langdata_dir ../langdata --fonts_dir /usr/share/fonts --fontlist "CuneiformNAOutline Medium" "CuneiformOB" "Segoe UI Historic" --output_dir .
