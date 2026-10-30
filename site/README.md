# The SWL website

The website for SWL: what SWL is, a quick start, where to find the sources, and the reference,
online and as a PDF. It is published at <https://seecr.github.io/swl/>.

It is a [Hugo](https://gohugo.io) site. The home page is `content/_index.md`; the layout is in
`layouts/` and the styles in `static/css/site.css`. The reference page and the PDF are made from
`../doc/reference.md`; the generated `content/reference.md` and `static/swl-reference.pdf` are
not in git.

## Building

You need `hugo` (extended, 0.120 or newer), `pandoc` and `xelatex` with the DejaVu fonts. On
macOS: `brew install hugo pandoc` and MacTeX or BasicTeX.

```sh
cd site
make          # site in public/, including public/swl-reference.pdf
make serve    # dev server on http://localhost:1313/swl/
make pdf      # only static/swl-reference.pdf
make clean
```

Extra Hugo options go in `HUGO_FLAGS`, e.g. `make serve HUGO_FLAGS="--bind 0.0.0.0"`.

## Publishing

`.github/workflows/pages.yml` publishes the site to GitHub Pages after each release: when the
"Publish to PyPI" workflow for a version tag has succeeded, the site is built from that tag, so
it shows the reference of the released version. It can also be run by hand from the Actions
tab ("Run workflow"); then it builds from the branch you pick.
