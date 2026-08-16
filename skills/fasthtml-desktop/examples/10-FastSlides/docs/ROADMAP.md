# FastSlides Roadmap — Frappe Slides feature comparison

FastSlides ports the core of [Frappe Slides](https://github.com/frappe/slides)
(3 doctypes: `Presentation`, `Slide`, `Reference Presentation`) to a FastHTML
demonstrator — and adds AI deck generation, which upstream doesn't have.

## Implemented ✅

| Capability | Upstream doctype(s) | FastSlides |
|---|---|---|
| Presentations | `Presentation` | `presentations` (title, subtitle, theme) |
| Slides | `Slide` | `slides` (position, title, Markdown body, layout) |
| Themed rendering | presentation theme | 4 gradient themes, 16:9 canvas |
| Slide editor | builder UI | thumbnails + live canvas + edit form |
| Present mode | present view | full-screen, keyboard-navigable slideshow |
| **AI deck generation** | *(not upstream)* | prompt → JSON deck → editor |

## Near-term roadmap 🔜

1. ✅ **Add / delete / reorder slides** (done) — plus
   new-slide, delete, and drag-to-reorder (`Slide.position`).
2. ✅ **Create a blank deck** (done).
3. **Per-deck theme switching** + a custom-colour theme.
4. **Images & media** — slide images/backgrounds (upload + layout variants).
5. **Speaker notes** — a notes field per slide, shown in a presenter view.
6. **Export** — PDF/PPTX export (the sibling FastClinic builds branded PDF decks
   via pandoc/WeasyPrint — reuse that pipeline).
7. **AI per-slide actions** — "improve this slide", "add a slide after",
   "make it shorter" inline in the editor.

## Later / out-of-scope 🗓️

- **Real-time collaborative editing** (multi-cursor) — needs an OT/CRDT layer.
- **Reference Presentation** — Frappe's template/clone-from mechanism.
- **Transitions & animations** beyond simple slide stepping.
- **Embed / public share links** with view analytics.

## Design notes

The headline is **AI deck generation**: `ai.generate_deck()` asks the model for a
strict JSON array of slides and validates each (`title`, `body`, `layout`) before
persisting — so a one-line prompt becomes an editable deck. The natural next step
is full slide CRUD (add/delete/reorder) so AI and manual editing compose freely,
plus PDF/PPTX export for sharing.
