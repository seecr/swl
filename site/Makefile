# The SWL website (Hugo), with the reference as a page and as a PDF.
#
#   make            build everything into public/
#   make serve      run the Hugo dev server (http://localhost:1313/)
#   make pdf        only the reference PDF
#
# Extra Hugo options go in HUGO_FLAGS, e.g. `make serve HUGO_FLAGS="--bind 0.0.0.0"`.
# The reference is ../doc/reference.md; the version is the latest tag of this repository.

SWL_DIR ?= ..

REFERENCE_MD := $(SWL_DIR)/doc/reference.md
SWL_VERSION   = $(shell git -C $(SWL_DIR) describe --tags 2>/dev/null || echo main)

.PHONY: all build serve pdf reference news clean

all: build

build: reference pdf news
	hugo --minify $(HUGO_FLAGS)

serve: reference pdf news
	hugo server $(HUGO_FLAGS)

reference: content/reference.md
pdf: static/swl-reference.pdf

# The banner on the home page: the highlights of the latest x.y release, from CHANGELOG.md
# (news.py). Made every time, as the version comes from the tags.
news:
	mkdir -p data
	python3 news.py $(SWL_DIR)/CHANGELOG.md "$(SWL_VERSION)" > data/news.json

# The reference page on the site: SWL's doc/reference.md with Hugo front matter.
content/reference.md: $(REFERENCE_MD)
	{ printf -- '---\ntitle: "SWL reference"\nversion: "%s"\n---\n\n' "$(SWL_VERSION)"; \
	  cat $(REFERENCE_MD); } > $@

# The PDF: pandoc turns the reference into Typst with pdf/reference.typ as template (title
# page, contents, styles), then typst makes the PDF. The title and the hand-made table of
# contents of reference.md are left out; the template makes both. reference.lua keeps
# each example on one page with the sentence that introduces it, and marks header rows.
static/swl-reference.pdf: $(REFERENCE_MD) pdf/reference.typ pdf/reference.lua pdf/seecr-logo.png
	awk 'NR == 1 && /^# / { next } /^- \[[^]]*\]\(#[^)]*\)$$/ { next } { print }' \
	    $(REFERENCE_MD) | \
	pandoc --from markdown+gfm_auto_identifiers-raw_html-raw_tex-tex_math_dollars-smart \
	    --shift-heading-level-by=-1 \
	    --to typst --template pdf/reference.typ --syntax-highlighting=idiomatic \
	    --lua-filter pdf/reference.lua \
	    --variable version="$(SWL_VERSION)" \
	    --output pdf/reference.out.typ
	typst compile --ignore-system-fonts pdf/reference.out.typ $@

clean:
	rm -rf public resources content/reference.md static/swl-reference.pdf pdf/reference.out.typ \
	    data/news.json .hugo_build.lock
