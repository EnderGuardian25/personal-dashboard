# Dashboard sync — index.html patch

Three small additions to `index.html` to wire it up to the sync backend.

Apply them in this order:

1. `1-style-block.css`  → paste at the END of the existing `<style>` block, just before `</style>`.
2. `2-header-html.html` → REPLACE the existing `<div class="hero-meta">…</div>` block with this.
3. `3-script-block.js`  → paste at the END of the existing `<script>` block, just before `</script>`.

After patching, every device that opens the dashboard will have a "SYNC OFF" badge in the header. Click it to enter the worker URL + sync token. From then on, your queue, learning progress, and selected track stay synchronised.

Status colours on the badge:
- grey = sync off / not configured
- blue = configured, idle
- amber pulsing = pushing / pulling
- green = last sync ok
- red = error (auth, network, etc.)
