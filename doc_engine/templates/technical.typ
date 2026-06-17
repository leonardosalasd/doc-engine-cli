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
  let accent-color = if accent == none { rgb("#7c3aed") } else { accent }
  let ink = rgb("#18181b")
  let muted = rgb("#71717a")
  let surface = rgb("#fafafa")
  let line-color = rgb("#e4e4e7")

  set document(author: author, title: title)

  set page(
    paper: "us-letter",
    margin: (top: 1.1in, bottom: 1.1in, left: 1.1in, right: 1.1in),
    header: context {
      if counter(page).get().first() > 1 [
        #set text(font: ("Cascadia Code", "Consolas"), size: 7.5pt, fill: muted)
        #stack(dir: ltr, spacing: 1fr, title, author)
        #v(-0.3em)
        #line(length: 100%, stroke: 0.5pt + line-color)
      ]
    },
    footer: context {
      set text(font: ("Cascadia Code", "Consolas"), size: 7.5pt, fill: muted)
      if branding {
        grid(
          columns: (1fr, auto),
          align(left)[#link("https://github.com/leonardosalasd/doc-engine-cli")[doc-engine-cli]],
          align(right)[#counter(page).display() / #context counter(page).final().first()],
        )
      } else {
        align(right)[#counter(page).display() / #context counter(page).final().first()]
      }
    },
  )

  set text(font: ("Inter", "Helvetica Neue", "Arial"), size: 10pt, fill: ink, lang: "en")
  set par(justify: true, leading: 0.68em, spacing: 1em)

  show raw.where(block: true): it => block(
    fill: surface,
    inset: (x: 14pt, y: 10pt),
    radius: 0pt,
    width: 100%,
    stroke: (left: 2.5pt + accent-color, rest: 0.5pt + line-color),
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 8.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => box(
    fill: surface,
    inset: (x: 4pt, y: 2pt),
    radius: 2pt,
    stroke: 0.5pt + line-color,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 9pt, it),
  )

  show heading.where(level: 1): it => block(width: 100%, sticky: true)[
    #v(1.4em)
    #block(fill: accent-color, inset: (x: 10pt, y: 7pt), radius: 3pt, width: 100%)[
      #set text(size: 14pt, weight: 700, fill: white)
      #it
    ]
    #v(0.5em)
  ]

  show heading.where(level: 2): it => block(sticky: true)[
    #set text(size: 12pt, weight: 700, fill: ink)
    #v(1em)
    #grid(
      columns: (auto, 1fr),
      gutter: 0.6em,
      align(horizon)[#box(width: 8pt, height: 8pt, fill: accent-color, radius: 1pt)],
      it,
    )
    #v(0.3em)
  ]

  show heading.where(level: 3): it => block(sticky: true)[
    #set text(size: 10.5pt, weight: 700, fill: accent-color, font: ("Cascadia Code", "Consolas"))
    #v(0.7em)
    #it
    #v(0.2em)
  ]

  block(width: 100%, fill: accent-color, inset: (x: 28pt, y: 36pt), radius: 4pt)[
    #set text(fill: white)
    #text(font: ("Cascadia Code", "Consolas"), size: 9pt, fill: white.transparentize(20%))[TECHNICAL DOCUMENT]
    #v(1.2em)
    #text(font: "Inter", size: 34pt, weight: 800, tracking: -1pt)[#title]
  ]
  v(2em)
  grid(
    columns: (auto, 1fr),
    gutter: 1em,
    text(weight: 600)[#author],
    align(right)[#text(fill: muted)[#date]],
  )
  if branding {
    v(0.6em)
    text(font: ("Cascadia Code", "Consolas"), size: 8pt, fill: muted)[doc-engine v#version]
  }
  pagebreak()

  show outline.entry.where(level: 1): it => {
    v(10pt, weak: true)
    strong(it)
  }
  outline(title: [Contents], indent: 1.4em, depth: 3)
  pagebreak()

  body

  if bibliography_file != none {
    pagebreak()
    bibliography(bibliography_file, style: "ieee")
  }
}
