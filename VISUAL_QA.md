# Document and visual checks

Final checks are dated 15 October 2026 and apply to version 3.0.

The canonical manuscript has 27 pages. The LaTeX build is required to have no compilation error, unresolved reference, unresolved citation warning or overfull box. Every page is inspected after the final build, with closer review of the title, theorem statements, strict-endpoint derivation, nonproportional-family calculation, tables, references and assurance note. Underfull table-cell diagnostics are acceptable only when no content is clipped or ambiguous.

The Markdown and HTML editions are regenerated from the final LaTeX source. Their section structure, author/year reference labels, equations, tables, figures and local links are checked against the PDF. Wide mathematics and tables may scroll inside their own containers, but the documents must not create page-level horizontal overflow at representative desktop and mobile widths.

All scientific figures derive from bound numerical inputs or certificates. They illustrate exact results; they are not the evidence for them. Release art and social thumbnails are separately required to be both informative and visually distinctive, and must not replace the scientific figures inside the paper.

Machine-readable results, including page count, link checks, text-integrity checks and final PDF SHA-256, are recorded in `results/document-qa.json` after the last build. This is visual and structural QA, not formal accessibility certification or screen-reader conformance testing.
