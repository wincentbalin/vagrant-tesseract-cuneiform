# Train Tesseract OCR for Akkadian language

LANG = akk
CORPUS = corpus-12pt.txt
LANGDATA_ROOT = ../langdata
FREQ_DAWG_SIZE = 100

FONTS := "CuneiformNAOutline Medium" "CuneiformOB" "CuneiformComposite" "Segoe UI Historic"
FONTSJOINED := CuneiformNAOutlineMedium CuneiformOB CuneiformComposite SegoeUIHistoric 
EXPOSURES := 0

BASENAMES := $(foreach b,$(FONTSJOINED),$(foreach e,$(EXPOSURES),$(LANG).$b.exp$e))
TIF_FILES := $(foreach b,$(BASENAMES),$b.tif)
BOX_FILES := $(foreach b,$(BASENAMES),$b.box)
TR_FILES := $(foreach b,$(BASENAMES),$b.tr)

TEXT2IMAGE_OPTS = --fonts_dir /usr/share/fonts --text $(CORPUS)

all: $(LANG).traineddata

clean:
	rm -f *.tr *.tif *.box $(LANG).*-dawg unicharset unicharset.metrics font_properties $(LANG).xheights $(LANG).unicharset $(LANG).training-text $(LANG).training-text.bigram_freqs $(LANG).training-text.unigram_freqs $(LANG).wordlist $(LANG).wordlist.freq $(LANG).word.bigrams $(LANG).shapetable $(LANG).inttemp $(LANG).pffmtable $(LANG).normproto

$(LANG).traineddata: $(LANG).word-dawg $(LANG).freq-dawg $(LANG).bigram-dawg $(LANG).normproto $(LANG).pffmtable
	combine_tessdata $(LANG)

$(LANG).pffmtable $(LANG).inttemp: font_properties $(LANG).unicharset $(TR_FILES)
	mftraining -F font_properties -U $(LANG).unicharset -O $(LANG).mfunicharset $(TR_FILES)
	mv pffmtable $(LANG).pffmtable
	mv inttemp $(LANG).inttemp
	mv shapetable $(LANG).shapetable
	mv $(LANG).mfunicharset $(LANG).unicharset

$(LANG).shapetable: font_properties $(LANG).unicharset $(LANG).xheights $(TR_FILES)
	shapeclustering -F font_properties -U $(LANG).unicharset -O $(LANG).mfunicharset -X $(LANG).xheights $(TR_FILES)
	mv shapetable $@

$(LANG).normproto: $(TR_FILES)
	cntraining $^
	mv normproto $@

$(LANG).bigram-dawg: $(LANG).wordlist $(LANG).unicharset
	wordlist2dawg $(LANG).word.bigrams $@ $(LANG).unicharset

$(LANG).freq-dawg: $(LANG).wordlist.freq $(LANG).unicharset
	wordlist2dawg $< $@ $(LANG).unicharset

$(LANG).word-dawg: $(LANG).wordlist $(LANG).unicharset
	wordlist2dawg $< $@ $(LANG).unicharset

$(LANG).wordlist.freq: $(LANG).wordlist
	head -n $(FREQ_DAWG_SIZE) $< > $@

$(LANG).wordlist $(LANG).word.bigrams $(LANG).training_text $(LANG).training_text.bigrams $(LANG).training_text.unigrams: $(CORPUS) create_dictdata.py
	env python3 ./create_dictdata.py -l $(LANG) -i $(CORPUS) -d .

%.tr: %.box
	tesseract $*.tif $* box.train.stderr # $*.train-log

font_properties:
	rm -f $@
	for f in $(FONTSJOINED); \
	do \
	  echo "$$f 0 0 0 0 0" >> $@; \
	done

$(LANG).xheights:
	rm -f $@
	for f in $(FONTSJOINED); \
	do \
	  xheight "$$f" >> $@; \
	done

$(LANG).unicharset: $(BOX_FILES)
	unicharset_extractor $^
	addmetrics $(FONTS) < unicharset > unicharset.metrics
	mv unicharset.metrics unicharset
	set_unicharset_properties -U unicharset -O $@ --script_dir=$(LANGDATA_ROOT)

# Font-dependent pattern rules
$(LANG).CuneiformNAOutlineMedium.exp%.box: $(CORPUS)
	text2image $(TEXT2IMAGE_OPTS) --outputbase $(LANG).CuneiformNAOutlineMedium.exp$* --font "CuneiformNAOutline Medium" --exposure $*

$(LANG).CuneiformOB.exp%.box: $(CORPUS)
	text2image $(TEXT2IMAGE_OPTS) --outputbase $(LANG).CuneiformOB.exp$* --font "CuneiformOB" --exposure $*

$(LANG).CuneiformComposite.exp%.box: $(CORPUS)
	text2image $(TEXT2IMAGE_OPTS) --outputbase $(LANG).CuneiformComposite.exp$* --font "CuneiformComposite" --exposure $*

$(LANG).SegoeUIHistoric.exp%.box: $(CORPUS)
	text2image $(TEXT2IMAGE_OPTS) --outputbase $(LANG).SegoeUIHistoric.exp$* --font "Segoe UI Historic" --exposure $*
