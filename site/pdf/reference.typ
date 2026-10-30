// Pandoc template (Typst) for the SWL reference PDF.
// Used by `make pdf`: pandoc fills in the body and the variables, typst makes the PDF.
// Fonts are the ones built into typst, so the PDF looks the same everywhere.

#let brand = rgb("#b5690a")      // Seecr orange, darkened to read on white (as on the site)
#let brand-logo = rgb("#faa21b") // Seecr orange as in the logo
#let link-color = rgb("#2d5bd3")
#let muted = rgb("#5f6670")
#let border = rgb("#dde1e6")
#let code-bg = rgb("#f4f5f7")
#let mono = "DejaVu Sans Mono"
#let version = [$version$]

// What pandoc's own typst template defines and its output may use.
#let horizontalrule = line(start: (25%, 0%), end: (75%, 0%), stroke: 0.5pt + border)
#show terms.item: it => block(breakable: false)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.5em, top: -0.4em))[#it.description]
]

#set document(title: [SWL reference], author: "Seecr")
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#set par(justify: false, leading: 0.62em, spacing: 0.9em)

// Code
#show raw: set text(font: mono, size: 0.82em)
#show raw.where(block: false): it => box(
  fill: code-bg, inset: (x: 2pt), outset: (y: 2.5pt), radius: 2pt, it,
)
#show raw.where(block: true): it => block(
  width: 100%, fill: code-bg, stroke: 0.5pt + border, radius: 4pt, inset: 8pt, it,
)

// Links and headings
#show link: set text(fill: link-color)
#show heading: set text(font: mono, fill: brand, weight: "semibold")
#show heading.where(level: 1): it => {
  v(1.2em, weak: true)
  block(below: 0.8em, stroke: (bottom: 0.5pt + border), inset: (bottom: 4pt), width: 100%,
    text(size: 1.35em, it.body))
}
#show heading.where(level: 2): it => block(above: 1.3em, below: 0.6em, text(size: 1.1em, it.body))

// Tables
#set table(stroke: (x, y) => (top: if y == 0 { 0.5pt + border }, bottom: 0.5pt + border),
           inset: (x: 5pt, y: 4pt))
// A table's header row is bold on a grey background, as on the site; reference.lua puts
// those rules around each table that has a header row (an empty one leaves pandoc out).
#let header-row(body) = {
  show table.cell.where(y: 0): set text(weight: "bold")
  set table(fill: (x, y) => if y == 0 { code-bg })
  body
}
#show table: set text(size: 0.92em)
#show figure.where(kind: table): set block(breakable: true)
#show figure.where(kind: table): set align(left)
#show table: set align(left)

// Title page
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm))
#page(header: none, footer: none)[
  #v(28%)
  #align(center)[
    #text(font: mono, size: 54pt, weight: "bold")[
      #text(fill: brand-logo, weight: "regular")[{{] swl #text(fill: brand-logo, weight: "regular")[}}]
    ]
    #v(0.6em)
    #text(size: 22pt)[Reference]
    #v(0.3em)
    #text(style: "italic", fill: muted)[interactive web apps in Python, without a JavaScript frontend]
    #v(1.6em)
    #text(font: mono, size: 10pt, fill: muted)[version #version · seecr.github.io/swl]
  ]
  #place(bottom + center, image("seecr-logo.png", height: 0.75cm))
]

// Other pages: a running header and page numbers
#set page(
  header: context {
    set text(size: 8.5pt, fill: muted, font: mono)
    [SWL reference #h(1fr) #version]
    v(-0.5em)
    line(length: 100%, stroke: 0.4pt + border)
  },
  footer: context align(center, text(size: 8.5pt, fill: muted, counter(page).display())),
)
#counter(page).update(1)

#outline(title: [Contents], depth: 2, indent: 1.2em)
#pagebreak()

$body$
