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
  let accent-color = if accent == none { rgb("#111827") } else { accent }
  let ink = rgb("#1f2937")
  let muted = rgb("#9ca3af")
  let surface = rgb("#f6f6f6")

  set document(author: author, title: title)

  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1in, right: 1in),
    footer: context {
      set text(font: "Inter", size: 8pt, fill: muted)
      if branding {
        grid(
          columns: (1fr, auto),
          align(left)[#link("https://github.com/leonardosalasd/doc-engine-cli")[doc-engine-cli]],
          align(right)[#counter(page).display()],
        )
      } else {
        align(center)[#counter(page).display()]
      }
    },
  )

  set text(font: ("Inter", "Helvetica Neue", "Arial"), size: 10.5pt, fill: ink, lang: "en")
  set par(justify: false, leading: 0.72em, spacing: 0.95em)

  show raw.where(block: true): it => block(
    fill: surface,
    inset: (x: 12pt, y: 9pt),
    radius: 3pt,
    width: 100%,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 8.5pt, fill: ink, it),
  )

  show raw.where(block: false): it => box(
    fill: surface,
    inset: (x: 4pt, y: 1pt),
    radius: 2pt,
    text(font: ("Cascadia Code", "Consolas", "Courier New"), size: 9pt, it),
  )

  show heading.where(level: 1): it => block[
    #set text(size: 15pt, weight: 700, fill: accent-color)
    #v(1.1em)
    #it
    #v(0.25em)
  ]

  show heading.where(level: 2): it => block[
    #set text(size: 12pt, weight: 700, fill: ink)
    #v(0.9em)
    #it
    #v(0.2em)
  ]

  show heading.where(level: 3): it => block[
    #set text(size: 10.5pt, weight: 600, fill: muted)
    #v(0.7em)
    #it
  ]

  block[
    #text(size: 24pt, weight: 800, fill: ink)[#title]
    #v(0.4em)
    #text(size: 10pt, fill: muted)[#author #h(0.6em) · #h(0.6em) #date]
    #v(0.6em)
    #line(length: 100%, stroke: 1pt + accent-color)
  ]
  v(1.2em)

  body

  if bibliography_file != none {
    v(1.5em)
    line(length: 100%, stroke: 0.5pt + muted)
    bibliography(bibliography_file, style: "ieee")
  }
}
