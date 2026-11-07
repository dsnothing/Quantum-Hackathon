---
name: slide-readability
description: Review and improve readability of an existing PowerPoint, preserving its visual identity and checking numerical and scientific claims. Use for slide appearance, legibility, or presentation audit requests.
---

# Slide readability

Use the available Presentations skill for importing, editing, rendering, and exporting. Work on a copy. Inspect every original slide before changing layouts.

Run `scripts/audit_pptx.py INPUT.pptx` with Python. Its report finds explicit small text and off-canvas geometry, but does not resolve theme fonts, inherited backgrounds, or actual text wrapping. Treat the report as triage, not visual proof.

For an illustrated background, inspect the text against the busiest region. Prefer a plain reading area and artwork beside it. Preserve source attribution and artwork proportions. Enlarge technical copy by shortening sentences and allocating more space before shrinking fonts. Use editable tables for comparisons. Keep exact run settings and extra precision in speaker notes when rounding does not change the conclusion.

For scientific results, keep expected score separate from best sampled score. Name the classical comparator and retain worse outcomes. Distinguish raw quantum results from any classical fallback, ideal simulation from hardware, and quality parity from speedup. Confirm travel direction against code when explaining directed networks.

Render every final slide and inspect at presentation size. Check clipping, table headings, color contrast, background competition, and footers. Confirm all reported numbers against a saved evidence file. Deliver the edited deck and state any material limitations. Never treat a passing XML audit as proof of readability.
