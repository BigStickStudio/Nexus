# Written by Richard Christopher, Copyright 2026 NeoTec Digital
PDFLATEX = pdflatex
MAIN = stable_chaos

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex $(wildcard figures/*.pdf)
	$(PDFLATEX) $(MAIN).tex
	$(PDFLATEX) $(MAIN).tex

clean:
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).toc

.PHONY: all clean
