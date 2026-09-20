# include <stdlib.ARKlight>
"""
Clip Reader -- paste Markdown from the clipboard, see it rendered
natively, and have it read aloud with text-to-speech.

Authored entirely in Python against ARKlight's component API, with
**no hand-written Kotlin/Java anywhere in this project**. The static
HTML/CSS/JS this file compiles to is packaged as a native Android app
purely by `arklight android scaffold`
(androidx.webkit.WebViewAssetLoader -- see docs/Backends/
ANDROID-BACKEND-IMPLEMENTATION.md in the ARKlight repo this project
builds against), and its generated `MainActivity.kt` is used exactly
as scaffolded, unmodified. Every capability the app needs -- clipboard
access, speech synthesis -- is reached through standard web-platform
APIs (`navigator.clipboard`, `window.speechSynthesis`) that Chromium
WebView (what the scaffolded project embeds) already implements on
top of the OS's own clipboard and TTS engine. There's no
JS-to-native bridge: the scaffolded project doesn't register one, and
this project doesn't add one.

Everything that has to happen at *runtime* against data ARKlight can't
see at compile time -- reading the clipboard, parsing arbitrary
Markdown, driving text-to-speech -- lives in the `ClipReaderRuntime`
script extension at the bottom of this file (ARKlight's documented
`script-extension` escape hatch, see docs/Foundational/
EXPERIMENTAL-APIS.md -- still plain JS shipped inside `arklight.js`,
nothing native). The component tree above it is the static shell that
JS then wires up and populates.
"""

from arklight.backend.script_extension import ScriptExtension

site = Site(
    name="clip-reader",
    max_width="46rem",
    font_family='"Literata", "Georgia", serif',
    lang="en",
)

# ---------------------------------------------------------------------------
# Design tokens / custom classes
# ---------------------------------------------------------------------------
# Kept intentionally close to what a reading/notes app actually ships
# with (Bear, GitHub's rendered Markdown, Obsidian's reading view): a
# quiet neutral chrome, one accent color reserved for the primary
# action, and a serif reading face for the rendered body so long-form
# text is comfortable rather than looking like an admin panel.

ACCENT = "#3d6b5c"
ACCENT_DARK = "#2b4d42"
INK = "#1c1c1e"
PAPER = "#fbfaf7"
MUTED = "#6b6a66"
BORDER = "#e4e1da"

site.style("app-shell", {
    # `android.edge_to_edge = True` in arklight.config.py draws this
    # WebView behind the status/nav bars, so the shell -- not just the
    # topbar/footer -- has to reserve safe-area space itself; a flat
    # `100vh` would let content sit under a bar instead.
    "min-height": "100dvh",
    "display": "flex",
    "flex-direction": "column",
    "background": PAPER,
    "color": INK,
    # Keeps a clipboard-triggered scroll bounce from rubber-banding
    # past the shell's own edges -- the one part of "feels like a
    # website" this app has no use for.
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
    "font-family": '"Inter", system-ui, sans-serif',
    "font-size": "1.05rem",
    "font-weight": "700",
    "letter-spacing": "-0.01em",
    "margin": "0",
    "color": INK,
})

site.style("tagline", {
    "font-family": '"Inter", system-ui, sans-serif',
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
    "font-family": '"Inter", system-ui, sans-serif',
})

site.style("btn", {
    "font-family": '"Inter", system-ui, sans-serif',
    "font-size": "0.85rem",
    "font-weight": "600",
    "padding": "0.55rem 0.95rem",
    "border-radius": "999px",
    "border": f"1px solid {BORDER}",
    "background": "#fff",
    "color": INK,
    "cursor": "pointer",
    # A hovered/focused state makes sense on desktop, where this same
    # build also runs in a plain browser -- but a WebView has no
    # cursor, so the tactile feedback that actually reads as "native"
    # there is a pressed-down state plus no lingering blue tap flash.
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
    # `accent-color` re-tints the browser's own native slider thumb/
    # track -- the platform control stays the platform control (no
    # reimplementing it in divs), it just picks up this app's accent
    # instead of the OS default blue.
    "accent-color": ACCENT,
    "width": "6rem",
    "touch-action": "manipulation",
})

site.style("status-bar", {
    "display": "flex",
    "justify-content": "space-between",
    "align-items": "baseline",
    "font-family": '"Inter", system-ui, sans-serif',
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
    "font-family": '"Inter", system-ui, sans-serif',
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
    "font-family": '"Inter", system-ui, sans-serif',
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
    "font-family": '"Inter", system-ui, sans-serif',
    "font-size": "0.82rem",
    "padding": "0.6rem 1.1rem",
    "border-radius": "999px",
    "transition": "transform 0.25s ease",
    "z-index": "50",
})

site.style("toast-visible", {
    "transform": "translateX(-50%) translateY(0)",
})


@site.page("/")
def home():
    return Page(
        Container(
            Header(
                Container(
                    Heading("Clip Reader", level=1, class_name="brand"),
                    Text(
                        "Markdown from your clipboard, rendered and read aloud.",
                        class_name="tagline",
                    ),
                ),
                class_name="topbar",
            ),
            Main(
                Section(
                    Button("Paste", id="btn-paste", class_name="btn btn-primary"),
                    Button("Clear", id="btn-clear", class_name="btn"),
                    Button("Listen", id="btn-speak", class_name="btn btn-accent"),
                    Button("Pause", id="btn-pause", class_name="btn"),
                    Button("Stop", id="btn-stop", class_name="btn"),
                    Container(class_name="toolbar-spacer"),
                    Container(
                        Label("Speed", for_="rate-range"),
                        Input(
                            type="range",
                            id="rate-range",
                            min="0.5",
                            max="1.8",
                            step="0.1",
                            value="1",
                            class_name="rate-slider",
                        ),
                        class_name="rate-control",
                    ),
                    class_name="toolbar",
                    id="toolbar",
                ),
                Container(
                    Text("Paste something to get started.", id="status-text"),
                    Text("", id="meta-text"),
                    class_name="status-bar",
                ),
                Container(
                    Container(
                        Text("📋", class_name="empty-state-icon"),
                        Heading("Nothing here yet", level=2),
                        Text(
                            "Copy some Markdown anywhere on your phone -- "
                            "notes, a README, a message -- then tap Paste."
                        ),
                        id="empty-state",
                        class_name="empty-state",
                    ),
                    Article(id="md-preview", class_name="md-preview hidden"),
                    class_name="reader-card",
                    id="reader-card",
                ),
                class_name="content",
            ),
            Footer(
                Text(
                    "Parsed and read on-device. Nothing you paste leaves your phone.",
                ),
                class_name="footer",
            ),
            Container(id="toast", class_name="toast"),
            class_name="app-shell",
        ),
        title="Clip Reader",
    )


# ---------------------------------------------------------------------------
# Runtime behavior -- everything ARKlight can't know at compile time.
# ---------------------------------------------------------------------------

class ClipReaderRuntime(ScriptExtension):
    """
    #include <expapilib.ARKlight>

    Hand-written JS appended to `arklight.js` (see
    `arklight.backend.script_extension`). Owns three jobs, each
    independent of the others, all through standard web-platform APIs
    only -- nothing here talks to a native bridge, because this
    project doesn't add one:

    1. Clipboard: `navigator.clipboard.readText()`. Chromium WebView
       (what `arklight android scaffold` embeds) implements this the
       same way desktop Chrome does; `WebViewAssetLoader` serving this
       app's assets under a fixed `https://appassets.androidplatform.
       net` origin (rather than `file://`) is what makes it a secure
       context the Clipboard API is willing to run in at all. Guarded
       with a plain feature check and a clear on-screen message when
       it isn't available, rather than silently doing nothing.
    2. Markdown -> DOM: a small, dependency-free Markdown renderer
       (headings, emphasis, code, links, images, lists, blockquotes,
       tables, rules) -- hand-rolled rather than pulled from a CDN,
       since the packaged app is fully offline and WebViewAssetLoader
       only ever serves this app's own bundled assets.
    3. Text-to-speech: `window.speechSynthesis` /
       `SpeechSynthesisUtterance` -- also implemented by Chromium
       WebView on top of the device's own TTS engine, so voices, rate
       control, and real pause/resume all come from the platform for
       free, no native code required.
    """

    script = r"""
<script>
(function () {
  "use strict";

  // -------------------------------------------------------------
  // 1. Markdown -> HTML (small, dependency-free, line-based)
  // -------------------------------------------------------------
  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderInline(text) {
    let s = escapeHtml(text);
    // Images before links (shares the same bracket syntax, image wins on `!`).
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g,
      '<img alt="$1" src="$2" title="$3" loading="lazy">');
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g,
      '<a href="$2" title="$3" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    s = s.replace(/(?<![A-Za-z0-9_])_([^_]+)_(?![A-Za-z0-9_])/g, "<em>$1</em>");
    s = s.replace(/~~([^~]+)~~/g, "<del>$1</del>");
    return s;
  }

  function isTableSeparator(line) {
    return /^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(line);
  }

  function splitRow(line) {
    let t = line.trim();
    if (t.startsWith("|")) t = t.slice(1);
    if (t.endsWith("|")) t = t.slice(0, -1);
    return t.split("|").map(function (c) { return c.trim(); });
  }

  function markdownToHtml(src) {
    const lines = src.replace(/\r\n?/g, "\n").split("\n");
    const out = [];
    let i = 0;
    let listStack = []; // {type: 'ul'|'ol', indent}

    function closeLists(toIndent) {
      while (listStack.length && listStack[listStack.length - 1].indent >= toIndent) {
        out.push("</" + listStack.pop().type + ">");
      }
    }

    while (i < lines.length) {
      const line = lines[i];

      if (!line.trim()) { closeLists(0); i++; continue; }

      // Fenced code block.
      const fence = line.match(/^\s*```(.*)$/);
      if (fence) {
        closeLists(0);
        const lang = fence[1].trim();
        const body = [];
        i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) { body.push(lines[i]); i++; }
        i++; // skip closing fence
        const cls = lang ? ' class="language-' + escapeHtml(lang) + '"' : "";
        out.push("<pre><code" + cls + ">" + escapeHtml(body.join("\n")) + "</code></pre>");
        continue;
      }

      // Table.
      if (line.includes("|") && lines[i + 1] && isTableSeparator(lines[i + 1])) {
        closeLists(0);
        const header = splitRow(line);
        i += 2;
        const rows = [];
        while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
          rows.push(splitRow(lines[i])); i++;
        }
        out.push("<table><thead><tr>" +
          header.map(function (h) { return "<th>" + renderInline(h) + "</th>"; }).join("") +
          "</tr></thead><tbody>" +
          rows.map(function (r) {
            return "<tr>" + r.map(function (c) { return "<td>" + renderInline(c) + "</td>"; }).join("") + "</tr>";
          }).join("") + "</tbody></table>");
        continue;
      }

      // Heading.
      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        closeLists(0);
        const level = heading[1].length;
        out.push("<h" + level + ">" + renderInline(heading[2].trim()) + "</h" + level + ">");
        i++; continue;
      }

      // Horizontal rule.
      if (/^\s*([-*_])\s*(\1\s*){2,}$/.test(line)) {
        closeLists(0);
        out.push("<hr>"); i++; continue;
      }

      // Blockquote (grouped).
      if (/^\s*>\s?/.test(line)) {
        closeLists(0);
        const quoteLines = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
          quoteLines.push(lines[i].replace(/^\s*>\s?/, "")); i++;
        }
        out.push("<blockquote>" + markdownToHtml(quoteLines.join("\n")) + "</blockquote>");
        continue;
      }

      // List item (ordered or unordered), with basic nesting by indent.
      const listItem = line.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
      if (listItem) {
        const indent = listItem[1].length;
        const marker = listItem[2];
        const type = /\d/.test(marker) ? "ol" : "ul";
        while (listStack.length && listStack[listStack.length - 1].indent > indent) {
          out.push("</" + listStack.pop().type + ">");
        }
        if (!listStack.length || listStack[listStack.length - 1].indent < indent) {
          out.push("<" + type + ">");
          listStack.push({ type: type, indent: indent });
        } else if (listStack[listStack.length - 1].type !== type) {
          out.push("</" + listStack.pop().type + ">");
          out.push("<" + type + ">");
          listStack.push({ type: type, indent: indent });
        }
        out.push("<li>" + renderInline(listItem[3]) + "</li>");
        i++; continue;
      }

      // Paragraph: collect contiguous plain lines.
      closeLists(0);
      const para = [line];
      i++;
      while (i < lines.length && lines[i].trim() &&
             !/^\s*(#{1,6})\s+/.test(lines[i]) &&
             !/^\s*```/.test(lines[i]) &&
             !/^\s*>\s?/.test(lines[i]) &&
             !/^(\s*)([-*+]|\d+[.)])\s+/.test(lines[i])) {
        para.push(lines[i]); i++;
      }
      out.push("<p>" + renderInline(para.join(" ").trim()) + "</p>");
    }
    closeLists(0);
    return out.join("\n");
  }

  function plainTextFor(md) {
    // What gets spoken -- strip Markdown syntax down to prose rather
    // than reading punctuation aloud.
    return md
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/!\[[^\]]*\]\([^)]+\)/g, " image. ")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/[*_~>#-]/g, " ")
      .replace(/\|/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  // -------------------------------------------------------------
  // 2. Clipboard -- standard Web Clipboard API only
  // -------------------------------------------------------------
  function readClipboard() {
    if (navigator.clipboard && navigator.clipboard.readText) {
      return navigator.clipboard.readText();
    }
    return Promise.reject(new Error("No clipboard access available."));
  }

  // -------------------------------------------------------------
  // 3. Text-to-speech -- standard Web Speech API only
  // -------------------------------------------------------------
  const tts = {
    supported: function () { return !!window.speechSynthesis; },
    speak: function (text, rate) {
      if (!this.supported()) return;
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = rate;
      utter.onstart = function () { setSpeakingState(true); };
      utter.onend = function () { setSpeakingState(false); };
      utter.onerror = function () { setSpeakingState(false); };
      window.speechSynthesis.speak(utter);
    },
    pause: function () {
      if (this.supported()) window.speechSynthesis.pause();
    },
    resume: function () {
      if (this.supported()) window.speechSynthesis.resume();
    },
    stop: function () {
      if (this.supported()) window.speechSynthesis.cancel();
    },
  };

  // -------------------------------------------------------------
  // Wiring
  // -------------------------------------------------------------
  let currentMarkdown = "";
  let speaking = false;
  let paused = false;

  function toast(msg) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("toast-visible");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove("toast-visible"); }, 2200);
  }

  function wordStats(text) {
    const words = text.split(/\s+/).filter(Boolean).length;
    const minutes = Math.max(1, Math.round(words / 200));
    return words + (words === 1 ? " word" : " words") + " · ~" + minutes +
      " min read · ~" + Math.max(1, Math.round(words / 150)) + " min to listen";
  }

  function setSpeakingState(isSpeaking) {
    speaking = isSpeaking;
    if (isSpeaking) paused = false;
    const statusText = document.getElementById("status-text");
    const btnSpeak = document.getElementById("btn-speak");
    const btnPause = document.getElementById("btn-pause");
    if (isSpeaking) {
      statusText.textContent = "Reading aloud…";
      statusText.classList.add("status-speaking");
      btnSpeak.textContent = "Restart";
      btnPause.textContent = "Pause";
    } else {
      statusText.classList.remove("status-speaking");
      statusText.textContent = paused
        ? "Paused."
        : currentMarkdown ? "Ready." : "Paste something to get started.";
      btnSpeak.textContent = "Listen";
    }
  }

  function renderMarkdown(md) {
    currentMarkdown = md || "";
    const empty = document.getElementById("empty-state");
    const preview = document.getElementById("md-preview");
    const metaText = document.getElementById("meta-text");

    if (!currentMarkdown.trim()) {
      empty.classList.remove("hidden");
      preview.classList.add("hidden");
      metaText.textContent = "";
      setSpeakingState(false);
      return;
    }

    preview.innerHTML = markdownToHtml(currentMarkdown);
    empty.classList.add("hidden");
    preview.classList.remove("hidden");
    metaText.textContent = wordStats(plainTextFor(currentMarkdown));
    setSpeakingState(false);
  }

  function wire() {
    const btnPaste = document.getElementById("btn-paste");
    const btnClear = document.getElementById("btn-clear");
    const btnSpeak = document.getElementById("btn-speak");
    const btnPause = document.getElementById("btn-pause");
    const btnStop = document.getElementById("btn-stop");
    const rateRange = document.getElementById("rate-range");

    btnPaste.addEventListener("click", function () {
      readClipboard().then(function (text) {
        if (!text || !text.trim()) { toast("Clipboard is empty."); return; }
        renderMarkdown(text);
        toast("Pasted from clipboard.");
      }).catch(function () {
        toast("Couldn't read the clipboard.");
      });
    });

    btnClear.addEventListener("click", function () {
      tts.stop();
      renderMarkdown("");
    });

    btnSpeak.addEventListener("click", function () {
      if (!currentMarkdown.trim()) { toast("Nothing to read yet."); return; }
      const rate = parseFloat(rateRange.value || "1");
      tts.speak(plainTextFor(currentMarkdown), rate);
      setSpeakingState(true);
    });

    btnPause.addEventListener("click", function () {
      if (speaking && !paused) {
        tts.pause();
        paused = true;
        speaking = false;
        btnPause.textContent = "Resume";
        document.getElementById("status-text").textContent = "Paused.";
        document.getElementById("status-text").classList.remove("status-speaking");
      } else if (paused) {
        tts.resume();
        paused = false;
        speaking = true;
        btnPause.textContent = "Pause";
        document.getElementById("status-text").textContent = "Reading aloud…";
        document.getElementById("status-text").classList.add("status-speaking");
      }
    });

    btnStop.addEventListener("click", function () {
      tts.stop();
      paused = false;
      btnPause.textContent = "Pause";
      setSpeakingState(false);
    });

    rateRange.addEventListener("change", function () {
      if (speaking && !paused) {
        const rate = parseFloat(rateRange.value || "1");
        tts.speak(plainTextFor(currentMarkdown), rate);
      }
    });

    renderMarkdown("");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
</script>
"""


site.register_script_extension(ClipReaderRuntime())
