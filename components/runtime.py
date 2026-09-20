"""
Runtime behavior -- everything ARKlight can't know at compile time.

Lives in components/ (not pages/) since it's a reusable, page-attached
behavior unit, imported and registered once from site.py.
"""

from arklight.backend.script_extension import ScriptExtension


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

