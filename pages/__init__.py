"""One module per route. Each exposes a plain function that returns a
`Page(...)` -- the real `@site.page(...)` decorators live in site.py,
which imports these and wires them up (see site.py for why)."""
