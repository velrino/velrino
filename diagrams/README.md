# Architecture diagrams

The portfolio diagrams share one Graphviz visual system: icon-led cards,
rounded panels, semantic flow colors, a 16:9 title band, 4K PNG output, and a
self-contained SVG with embedded icons.

Each product owns its topology in a dedicated folder:

- `adapta-midia/architecture.py`
- `goatvpn/architecture.py`
- `wpp-ai/architecture.py`

Render any diagram from the repository root with `uv`; dependencies are
declared inside each script:

```bash
uv run diagrams/adapta-midia/architecture.py
uv run diagrams/goatvpn/architecture.py
uv run diagrams/wpp-ai/architecture.py
```

Every script creates `architecture.png` and `architecture.svg` beside its
source and copies the PNG to the matching folder under `assets/`, where the
profile README already references it.
