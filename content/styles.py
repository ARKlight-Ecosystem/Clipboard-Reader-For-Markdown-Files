"""
Design tokens + `site.style(...)` registrations for Clip Reader.

`site.style()` needs the live `Site()` instance, so it can't be pure
data the way the rest of content/ is -- this module's one exception is
`register(site)`, called once from site.py right after `Site()` is
constructed. Everything else here (the color constants) is plain data,
importable from components/ or pages/ wherever a token is needed
outside a stylesheet rule (e.g. an inline `style=` prop).

Kept intentionally close to what a reading/notes app actually ships
with (Bear, GitHub's rendered Markdown, Obsidian's reading view): a
quiet neutral chrome, one accent color reserved for the primary
action, and a serif reading face for the rendered body so long-form
text is comfortable rather than looking like an admin panel.
"""

from __future__ import annotations

ACCENT = "#3d6b5c"
ACCENT_DARK = "#2b4d42"
INK = "#1c1c1e"
PAPER = "#fbfaf7"
MUTED = "#6b6a66"
BORDER = "#e4e1da"

_SANS = '"Inter", system-ui, sans-serif'


def register(site) -> None:
    """Register every named class this app's components reference."""

    site.style("app-shell", {
        # `android.edge_to_edge = True` in arklight.config.py draws
        # this WebView behind the status/nav bars, so the shell --
        # not just the topbar/footer -- has to reserve safe-area
        # space itself; a flat `100vh` would let content sit under a
        # bar instead.
        "min-height": "100dvh",
        "display": "flex",
        "flex-direction": "column",
        "background": PAPER,
        "color": INK,
        # Keeps a clipboard-triggered scroll bounce from
        # rubber-banding past the shell's own edges -- the one part
        # of "feels like a website" this app has no use for.
        "overscroll-behavior-y": "contain",
    })

    site.style("topbar", {
        "position": "sticky",
        "top": "0",
        "z-index": "10",
        "padding": "calc(1.1rem + env(safe-area-inset-top, 0px)) 1.25rem 1.1rem",
        "background": "rgba(251, 250, 247, 0.92)",
        "backdrop-filter": "blur(8px)",
        "border-bottom": f"1px solid {BORDER}",
    })

    site.style("brand", {
        "font-family": _SANS,
        "font-size": "1.05rem",
        "font-weight": "700",
        "letter-spacing": "-0.01em",
        "margin": "0",
        "color": INK,
    })

    site.style("tagline", {
        "font-family": _SANS,
        "font-size": "0.8rem",
        "color": MUTED,
        "margin-top": "0.15rem",
    })

    site.style("content", {
        "flex": "1",
        "width": "100%",
        "padding": "1rem 1.1rem 2.5rem",
    })

    site.style("toolbar", {
        "display": "flex",
        "flex-wrap": "wrap",
        "align-items": "center",
        "gap": "0.5rem",
        "font-family": _SANS,
    })

    site.style("btn", {
        "font-family": _SANS,
        "font-size": "0.85rem",
        "font-weight": "600",
        "padding": "0.55rem 0.95rem",
        "border-radius": "999px",
        "border": f"1px solid {BORDER}",
        "background": "#fff",
        "color": INK,
        "cursor": "pointer",
        # A hovered/focused state makes sense on desktop, where this
        # same build also runs in a plain browser -- but a WebView
        # has no cursor, so the tactile feedback that actually reads
        # as "native" there is a pressed-down state plus no
        # lingering blue tap flash.
        "-webkit-tap-highlight-color": "transparent",
        "touch-action": "manipulation",
        "-webkit-user-select": "none",
        "user-select": "none",
        "transition": "transform 0.08s ease, background 0.15s ease",
        ":hover:background": "#f2f1eb",
        ":active:transform": "scale(0.96)",
        ":active:background": "#ece9e1",
        ":disabled:opacity": "0.45",
    })

    site.style("btn-primary", {
        "background": ACCENT,
        "border": f"1px solid {ACCENT}",
        "color": "#fff",
        ":hover:background": ACCENT_DARK,
    })

    site.style("btn-accent", {
        "background": "#fff",
        "border": f"1px solid {ACCENT}",
        "color": ACCENT_DARK,
        ":hover:background": "#eef4f1",
    })

    site.style("toolbar-spacer", {
        "flex": "1 1 auto",
        "min-width": "0.5rem",
    })

    site.style("rate-control", {
        "display": "flex",
        "align-items": "center",
        "gap": "0.5rem",
        "font-size": "0.78rem",
        "color": MUTED,
    })

    site.style("rate-slider", {
        # `accent-color` re-tints the browser's own native slider
        # thumb/track -- the platform control stays the platform
        # control (no reimplementing it in divs), it just picks up
        # this app's accent instead of the OS default blue.
        "accent-color": ACCENT,
        "width": "6rem",
        "touch-action": "manipulation",
    })

    site.style("status-bar", {
        "display": "flex",
        "justify-content": "space-between",
        "align-items": "baseline",
        "font-family": _SANS,
        "font-size": "0.78rem",
        "color": MUTED,
        "margin": "0.9rem 0.1rem 0.6rem",
    })

    site.style("status-speaking", {
        "color": ACCENT_DARK,
        "font-weight": "600",
    })

    site.style("reader-card", {
        "background": "#fff",
        "border": f"1px solid {BORDER}",
        "border-radius": "1rem",
        "padding": "1.5rem",
        "box-shadow": "0 1px 2px rgba(28, 28, 30, 0.04)",
        "min-height": "40vh",
    })

    site.style("empty-state", {
        "text-align": "center",
        "padding": "3rem 1rem",
        "color": MUTED,
        "font-family": _SANS,
    })

    site.style("empty-state-icon", {
        "font-size": "2.25rem",
        "margin-bottom": "0.75rem",
        "opacity": "0.6",
    })

    site.style("md-preview", {
        "line-height": "1.7",
        "font-size": "1.05rem",
        "word-wrap": "break-word",
    })

    site.style("hidden", {
        "display": "none",
    })

    site.style("speaking-highlight", {
        "background": "#fff2c4",
        "border-radius": "0.2rem",
    })

    site.style("footer", {
        "text-align": "center",
        "padding": "1rem 1rem calc(1rem + env(safe-area-inset-bottom, 0px))",
        "font-family": _SANS,
        "font-size": "0.72rem",
        "color": MUTED,
    })

    site.style("toast", {
        "position": "fixed",
        "left": "50%",
        "bottom": "1.5rem",
        "transform": "translateX(-50%) translateY(120%)",
        "background": INK,
        "color": "#fff",
        "font-family": _SANS,
        "font-size": "0.82rem",
        "padding": "0.6rem 1.1rem",
        "border-radius": "999px",
        "transition": "transform 0.25s ease",
        "z-index": "50",
    })

    site.style("toast-visible", {
        "transform": "translateX(-50%) translateY(0)",
    })
