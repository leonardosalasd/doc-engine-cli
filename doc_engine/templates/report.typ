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
  let accent-color = if accent == none { rgb("#1d4ed8") } else { accent }
  let ink = rgb("#1a1a1a")
  let muted = rgb("#71717a")
  let rule = rgb("#e4e4e7")

  let serif = ("Libertinus Serif", "New Computer Modern", "Georgia", "Times New Roman")
  let mono = ("DejaVu Sans Mono", "Cascadia Code", "Courier New")

  set document(author: author, title: title)

  // Wide margins and a short measure: roughly 65 characters a line, which is
  // the range that stays comfortable to read for pages at a time.
  set page(
    paper: paper,
    margin: (top: 1.4in, bottom: 1.4in, left: 1.6in, right: 1.6in),
    header: context {
      if counter(page).get().first() > 1 [
        #set text(font: serif, size: 9pt, fill: muted)
        #grid(
          columns: (1fr, auto),
          align(left)[#title],
          align(right)[#author],
        )
        #v(-0.5em)
        #line(length: 100%, stroke: 0.5pt + rule)
      ]
    },
    footer: context {
      set text(font: serif, size: 9pt, fill: muted)
      if branding {
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

  set text(font: serif, size: 12pt, fill: ink, lang: "en")
  set par(justify: true, leading: 0.95em, spacing: 1.5em)

  show heading: set block(above: 2.4em, below: 1.1em)

  show heading.where(level: 1): it => block(width: 100%, sticky: true)[
    #set text(size: 19pt, weight: 600, fill: ink)
    #it
    #v(0.5em)
    #line(length: 3.5em, stroke: 2pt + accent-color)
  ]

  show heading.where(level: 2): it => block(sticky: true)[
    #set text(size: 14pt, weight: 600, fill: accent-color)
    #it
  ]

  show heading.where(level: 3): it => block(sticky: true)[
    #set text(size: 12pt, weight: 600, fill: ink)
    #it
  ]

  show raw.where(block: true): it => block(
    fill: rgb("#fafafa"),
    inset: (x: 14pt, y: 12pt),
    radius: 3pt,
    width: 100%,
    stroke: 0.5pt + rule,
    text(font: mono, size: 9.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => box(
    fill: rgb("#f4f4f5"),
    inset: (x: 4pt, y: 2pt),
    radius: 2pt,
    text(font: mono, size: 10pt, it),
  )

  show figure.caption: set text(size: 10pt, fill: muted)
  show link: set text(fill: accent-color)

  align(left + horizon)[
    #v(-12%)
    #line(length: 2.5em, stroke: 3pt + accent-color)
    #v(1.5em)
    #text(size: 30pt, weight: 600, fill: ink)[#title]
    #if subtitle != "" [
      #v(0.7em)
      #text(size: 15pt, fill: muted)[#subtitle]
    ]
    #v(2.5em)
    #text(size: 12pt, weight: 600)[#author]
    #v(0.4em)
    #text(size: 11pt, fill: muted)[#date]
    #if branding [
      #v(4em)
      #text(size: 9.5pt, fill: muted)[Typeset with doc-engine v#version]
    ]
  ]
  pagebreak()

  show outline.entry.where(level: 1): it => {
    v(14pt, weak: true)
    strong(it)
  }
  outline(title: [Contents], indent: 1.6em, depth: 3)
  pagebreak()

  body

  if bibliography_file != none {
    pagebreak()
    bibliography(bibliography_file, style: "ieee")
  }
}
