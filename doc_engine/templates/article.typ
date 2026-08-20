#let setup_doc(
  title: "",
  subtitle: "",
  author: "Anonymous",
  date: datetime.today().display(),
  bibliography_file: none,
  accent: none,
  branding: true,
  version: "",
  paper: "a4",
  ..options,
  body,
) = {
  let accent-color = if accent == none { rgb("#1f2937") } else { accent }
  let ink = rgb("#111111")
  let muted = rgb("#6b7280")

  // New Computer Modern and DejaVu Sans Mono ship with Typst, so this renders
  // the same on a bare Linux container as it does on a laptop full of fonts.
  let serif = ("New Computer Modern", "Libertinus Serif", "Times New Roman")
  let mono = ("DejaVu Sans Mono", "Cascadia Code", "Courier New")

  set document(author: author, title: title)

  set page(
    paper: paper,
    margin: (top: 1in, bottom: 1in, left: 1.25in, right: 1.25in),
    footer: context {
      set text(font: serif, size: 9pt, fill: muted)
      if branding and counter(page).get().first() == 1 {
        grid(
          columns: (1fr, auto, 1fr),
          align(left)[#link("https://github.com/leonardosalasd/doc-engine-cli")[doc-engine-cli]],
          align(center)[#counter(page).display()],
          [],
        )
      } else {
        align(center)[#counter(page).display()]
      }
    },
  )

  set text(font: serif, size: 11pt, fill: ink, lang: "en")
  set par(justify: true, leading: 0.62em, first-line-indent: 1.5em, spacing: 0.62em)

  // The first `#` heading becomes the document title, so a file's real sections
  // usually start at `##`. Dropping the levels that never appear keeps them
  // numbered 1, 2, 3 instead of 0.1, 0.2, 0.3.
  set heading(numbering: (..levels) => {
    let parts = levels.pos()
    while parts.len() > 1 and parts.first() == 0 {
      parts = parts.slice(1)
    }
    if parts.first() == 0 { none } else { numbering("1.1", ..parts) }
  })
  show heading: set block(above: 1.6em, below: 0.9em)

  show heading.where(level: 1): it => block(sticky: true)[
    #set text(size: 12.5pt, weight: 700, fill: ink)
    #it
  ]

  show heading.where(level: 2): it => block(sticky: true)[
    #set text(size: 11.5pt, weight: 700, fill: accent-color)
    #it
  ]

  show heading.where(level: 3): it => block(sticky: true)[
    #set text(size: 11pt, weight: 400, style: "italic", fill: ink)
    #it
  ]

  show raw.where(block: true): it => block(
    inset: (x: 10pt, y: 8pt),
    width: 100%,
    stroke: (left: 1.5pt + accent-color),
    text(font: mono, size: 8.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => text(font: mono, size: 9pt, it)

  show figure.caption: set text(size: 9.5pt, fill: muted)

  // A LaTeX-style title block at the top of the first page, not a cover sheet.
  align(center)[
    #v(1em)
    #text(size: 17pt, weight: 700)[#title]
    #if subtitle != "" [
      #v(0.5em)
      #text(size: 12pt, style: "italic", fill: muted)[#subtitle]
    ]
    #v(1.1em)
    #text(size: 11pt)[#author]
    #v(0.35em)
    #text(size: 10pt, fill: muted)[#date]
    #if branding [
      #v(0.35em)
      #text(size: 8.5pt, fill: muted)[typeset with doc-engine v#version]
    ]
    #v(1.8em)
  ]

  set align(left)
  outline(title: [Contents], indent: 1.2em, depth: 3)
  v(1.5em)

  body

  if bibliography_file != none {
    v(1.5em)
    bibliography(bibliography_file, style: "ieee")
  }
}
