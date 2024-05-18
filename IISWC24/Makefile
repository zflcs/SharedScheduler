# Makefile used for iiswc24example 2024/05/14 version V1.0

PAPER = iiswc24example
TEX = $(wildcard *.tex)
BIB = reference.bib
FIGS = $(wildcard figs/*.png)

.PHONY: all clean

all: $(PAPER).pdf

$(PAPER).pdf: $(TEX) $(BIB) $(FIGS)
	pdflatex $(PAPER)
	bibtex $(PAPER)
	pdflatex $(PAPER)
	pdflatex $(PAPER)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PAPER).pdf
