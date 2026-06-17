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
  let accent-color = if accent == none { rgb("#0ea5e9") } else { accent }
  let ink = rgb("#1e293b")
  let muted = rgb("#94a3b8")
  let surface = rgb("#f1f5f9")

  set document(author: author, title: title)

  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1.3in, right: 1.3in),
    footer: context {
      set text(font: "Inter", size: 8pt, fill: muted)
      if branding {
        grid(
          columns: (1fr, auto),
          align(left)[#link("https://github.com/leonardosalasd/doc-engine-cli")[doc-engine-cli]],
          align(right)[#counter(page).display()],
        )
      } else {
        align(right)[#counter(page).display()]
      }
    },
  )

  set text(font: ("Inter", "Helvetica Neue", "Arial"), size: 10.5pt, fill: ink, lang: "en")
  set par(justify: false, leading: 0.8em, spacing: 1.1em)

  show raw.where(block: true): it => block(
    fill: surface,
    inset: (x: 16pt, y: 12pt),
    radius: 8pt,
    width: 100%,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 8.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => box(
    fill: surface,
    inset: (x: 5pt, y: 2pt),
    radius: 3pt,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 9pt, fill: accent-color, it),
  )

  show heading.where(level: 1): it => block(width: 100%)[
    #v(1.6em)
    #text(size: 9pt, weight: 700, fill: accent-color, tracking: 2pt)[#upper[Section]]
    #v(0.2em)
    #set text(size: 22pt, weight: 800, fill: ink)
    #it
    #v(0.5em)
  ]

  show heading.where(level: 2): it => block[
    #set text(size: 14pt, weight: 700, fill: ink)
    #v(1em)
    #it
    #v(0.3em)
  ]

  show heading.where(level: 3): it => block[
    #set text(size: 11.5pt, weight: 600, fill: accent-color)
    #v(0.7em)
    #it
    #v(0.2em)
  ]

  align(left + horizon)[
    #v(-8%)
    #line(length: 18%, stroke: 3pt + accent-color)
    #v(1.2em)
    #text(size: 44pt, weight: 800, tracking: -2pt, fill: ink)[#title]
    #v(2em)
    #grid(
      columns: (auto, auto),
      gutter: 1.5em,
      text(size: 11pt, weight: 600, fill: ink)[#author],
      text(size: 11pt, fill: muted)[#date],
    )
    #if branding [
      #v(4em)
      #text(size: 9pt, fill: muted)[Built with #text(weight: 600, fill: accent-color)[doc-engine v#version]]
    ]
    #pagebreak()
  ]

  show outline.entry.where(level: 1): it => {
    v(12pt, weak: true)
    strong(it)
  }
  outline(title: [Contents], indent: 1.2em, depth: 2)
  pagebreak()

  body

  if bibliography_file != none {
    pagebreak()
    bibliography(bibliography_file, style: "ieee")
  }
}
