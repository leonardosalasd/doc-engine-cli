#let setup_doc(
  title: "",
  author: "Anonymous",
  date: datetime.today().display(),
  bibliography_file: none,
  accent: none,
  branding: true,
  version: "",
  body,
) = {
  let accent-color = if accent == none { rgb("#7a1f2b") } else { accent }
  let ink = rgb("#2b2b2b")
  let muted = rgb("#8a8a8a")
  let surface = rgb("#f5f2ed")

  set document(author: author, title: title)

  set page(
    paper: "us-letter",
    margin: (top: 1.3in, bottom: 1.3in, left: 1.4in, right: 1.4in),
    header: context {
      if counter(page).get().first() > 1 [
        #set text(font: ("Linux Libertine", "Times New Roman"), size: 9pt, fill: muted, style: "italic")
        #align(center)[#title]
      ]
    },
    footer: context {
      set text(font: ("Linux Libertine", "Times New Roman"), size: 9pt, fill: muted)
      align(center)[#counter(page).display("— i —")]
    },
  )

  set text(font: ("Linux Libertine", "New Computer Modern", "Times New Roman"), size: 11.5pt, fill: ink, lang: "en")
  set par(justify: true, leading: 0.75em, first-line-indent: 1.4em, spacing: 0.75em)

  show heading: set text(font: ("Linux Libertine", "Times New Roman"))

  show raw.where(block: true): it => block(
    fill: surface,
    inset: (x: 14pt, y: 10pt),
    radius: 2pt,
    width: 100%,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 8.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => box(
    fill: surface,
    inset: (x: 4pt, y: 1pt),
    radius: 2pt,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 9pt, it),
  )

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    block(width: 100%)[
      #v(2em)
      #align(center)[
        #text(size: 10pt, weight: 400, fill: accent-color, tracking: 3pt)[#upper[Chapter]]
        #v(0.6em)
        #set text(size: 22pt, weight: 700, fill: ink, style: "italic")
        #it
      ]
      #v(0.6em)
      #align(center)[#line(length: 30%, stroke: 0.75pt + accent-color)]
      #v(1.4em)
    ]
  }

  show heading.where(level: 2): it => block[
    #set text(size: 14pt, weight: 700, fill: ink)
    #v(1em)
    #it
    #v(0.3em)
  ]

  show heading.where(level: 3): it => block[
    #set text(size: 12pt, weight: 700, fill: accent-color, style: "italic")
    #v(0.7em)
    #it
    #v(0.2em)
  ]

  align(center + horizon)[
    #line(length: 40%, stroke: 0.75pt + accent-color)
    #v(1.5em)
    #text(size: 32pt, weight: 700, fill: ink, style: "italic")[#title]
    #v(1.5em)
    #line(length: 40%, stroke: 0.75pt + accent-color)
    #v(3em)
    #text(size: 13pt, fill: ink)[#author]
    #v(0.5em)
    #text(size: 11pt, fill: muted, style: "italic")[#date]
    #if branding [
      #v(6em)
      #text(size: 9pt, fill: muted)[Set with #text(style: "italic")[doc-engine v#version]]
    ]
  ]
  pagebreak()

  show outline.entry.where(level: 1): it => {
    v(11pt, weak: true)
    strong(it)
  }
  outline(title: [Contents], indent: 1.5em, depth: 3)

  body

  if bibliography_file != none {
    pagebreak()
    bibliography(bibliography_file, style: "ieee")
  }
}
