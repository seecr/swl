# The SWL website (Hugo), with the reference as a page and as a PDF.
#
#   make            build everything into public/
#   make serve      run the Hugo dev server (http://localhost:1313/swl/)
#   make pdf        only the reference PDF
#
# Extra Hugo options go in HUGO_FLAGS, e.g. `make serve HUGO_FLAGS="--bind 0.0.0.0"`.
# The reference is ../doc/reference.md; the version is the latest tag of this repository.

SWL_DIR ?= ..

REFERENCE_MD := $(SWL_DIR)/doc/reference.md
SWL_VERSION   = $(shell git -C $(SWL_DIR) describe --tags 2>/dev/null || echo main)

.PHONY: all build serve pdf reference clean

all: build

build: reference pdf
	hugo --minify $(HUGO_FLAGS)

serve: reference pdf
	hugo server $(HUGO_FLAGS)

reference: content/reference.md
pdf: static/swl-reference.pdf

# The reference page on the site: SWL's doc/reference.md with Hugo front matter.
content/reference.md: $(REFERENCE_MD)
	{ printf -- '---\ntitle: "SWL reference"\nversion: "%s"\n---\n\n' "$(SWL_VERSION)"; \
	  cat $(REFERENCE_MD); } > $@

# The PDF: pandoc turns the reference into Typst with pdf/reference.typ as template (title
# page, contents, styles), then typst makes the PDF. The title and the hand-made table of
# contents of reference.md are left out; the template makes both.
static/swl-reference.pdf: $(REFERENCE_MD) pdf/reference.typ pdf/seecr-logo.png
	awk 'NR == 1 && /^# / { next } /^- \[[^]]*\]\(#[^)]*\)$$/ { next } { print }' \
	    $(REFERENCE_MD) | \
	pandoc --from markdown+gfm_auto_identifiers-raw_html-raw_tex-tex_math_dollars-smart \
	    --shift-heading-level-by=-1 \
	    --to typst --template pdf/reference.typ --syntax-highlighting=idiomatic \
	    --variable version="$(SWL_VERSION)" \
	    --output pdf/reference.out.typ
	typst compile --ignore-system-fonts pdf/reference.out.typ $@

clean:
	rm -rf public resources content/reference.md static/swl-reference.pdf pdf/reference.out.typ \
	    .hugo_build.lock
