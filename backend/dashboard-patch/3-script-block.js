  // ====== CROSS-DEVICE SYNC ======
  // Pulls/pushes the dashboard.* localStorage state to the backend Worker
  // so reading queue, learning progress, and track filter follow you between
  // devices. Falls back gracefully if offline / not configured.
  (function syncModule() {
    const SYNC_URL_KEY   = "dashboard.syncUrl";
    const SYNC_TOKEN_KEY = "dashboard.syncToken";
    const STATE_KEYS     = ["dashboard.queue", "dashboard.learning", "dashboard.track"];
    const DEBOUNCE_MS    = 600;

    const btn   = document.getElementById("sync-btn");
    const label = document.getElementById("sync-label");

    let syncUrl   = localStorage.getItem(SYNC_URL_KEY) || "";
    let syncToken = localStorage.getItem(SYNC_TOKEN_KEY) || "";
    let suppressPush = false;
    let pushTimer = null;

    function configured() { return !!syncUrl && !!syncToken; }

    function setStatus(s, msg) {
      btn.setAttribute("data-status", s);
      const labels = {
        off:          "SYNC OFF",
        idle:         "SYNC READY",
        syncing:      "SYNCING…",
        synced:       "SYNCED",
        error:        "SYNC ERROR",
        unauthorized: "BAD TOKEN",
      };
      label.textContent = msg || labels[s] || s.toUpperCase();
    }

    function rerenderAfterPull() {
      // These are the existing init/render functions defined elsewhere in this script.
      try { renderQueue();         } catch (e) {}
      try { refreshSaveButtons();  } catch (e) {}
      try { updateProgressRing();  } catch (e) {}
      const track = localStorage.getItem("dashboard.track");
      if (track && ["all", "cyber", "design"].includes(track)) {
        try { applyTrack(track); } catch (e) {}
      }
      // Re-sync learning-path checkbox visual state
      document.querySelectorAll("#resource-list .resource").forEach(item => {
        const key = item.dataset.key;
        const check = item.querySelector("[data-check]");
        const state = JSON.parse(localStorage.getItem("dashboard.learning") || "{}");
        const done = !!state[key];
        if (check) check.checked = done;
        item.classList.toggle("done", done);
      });
    }

    async function pullState() {
      if (!configured()) { setStatus("off"); return; }
      setStatus("syncing");
      try {
        const r = await fetch(syncUrl.replace(/\/$/, "") + "/api/state", {
          headers: { Authorization: "Bearer " + syncToken },
          cache: "no-store",
        });
        if (r.status === 401) { setStatus("unauthorized"); return; }
        if (!r.ok)            { setStatus("error", "HTTP " + r.status); return; }

        const data = await r.json();
        suppressPush = true;
        try {
          if (data && Array.isArray(data.queue)) {
            localStorage.setItem("dashboard.queue", JSON.stringify(data.queue));
          }
          if (data && data.learning && typeof data.learning === "object") {
            localStorage.setItem("dashboard.learning", JSON.stringify(data.learning));
          }
          if (data && typeof data.track === "string") {
            localStorage.setItem("dashboard.track", data.track);
          }
        } finally { suppressPush = false; }

        rerenderAfterPull();
        setStatus("synced");
      } catch (e) {
        setStatus("error", "OFFLINE?");
      }
    }

    function pushState() {
      if (!configured() || suppressPush) return;
      clearTimeout(pushTimer);
      pushTimer = setTimeout(async () => {
        setStatus("syncing");
        const payload = {
          queue:    JSON.parse(localStorage.getItem("dashboard.queue") || "[]"),
          learning: JSON.parse(localStorage.getItem("dashboard.learning") || "{}"),
          track:    localStorage.getItem("dashboard.track") || "all",
        };
        try {
          const r = await fetch(syncUrl.replace(/\/$/, "") + "/api/state", {
            method:  "PUT",
            headers: {
              "Content-Type":  "application/json",
              Authorization:   "Bearer " + syncToken,
            },
            body: JSON.stringify(payload),
          });
          if (r.status === 401) { setStatus("unauthorized"); return; }
          setStatus(r.ok ? "synced" : "error", r.ok ? null : "HTTP " + r.status);
        } catch (e) {
          setStatus("error", "OFFLINE?");
        }
      }, DEBOUNCE_MS);
    }

    // Intercept localStorage.setItem so any state-key write triggers a push.
    // This means we don't have to touch the existing queue/learning/track code.
    const origSet = localStorage.setItem.bind(localStorage);
    localStorage.setItem = function patchedSet(k, v) {
      origSet(k, v);
      if (STATE_KEYS.includes(k)) pushState();
    };

    // Connect / re-connect device dialog.
    btn.addEventListener("click", async () => {
      if (configured()) {
        const choice = prompt(
          "Sync is configured.\n\n" +
          "Type 'pull' to re-fetch from server.\n" +
          "Type 'disconnect' to forget the token on this device.\n" +
          "Leave blank to cancel.",
          ""
        );
        if (choice === null) return;
        if (choice.trim().toLowerCase() === "disconnect") {
          localStorage.removeItem(SYNC_URL_KEY);
          localStorage.removeItem(SYNC_TOKEN_KEY);
          syncUrl = ""; syncToken = "";
          setStatus("off");
          return;
        }
        if (choice.trim().toLowerCase() === "pull") {
          pullState();
        }
        return;
      }

      const url = prompt(
        "Worker URL (e.g. https://dashboard-sync.<you>.workers.dev):",
        syncUrl
      );
      if (url === null || !url.trim()) return;

      const token = prompt("Sync token (the one you set via `wrangler secret put SYNC_TOKEN`):", "");
      if (token === null || !token.trim()) return;

      syncUrl   = url.trim().replace(/\/$/, "");
      syncToken = token.trim();
      origSet(SYNC_URL_KEY,   syncUrl);
      origSet(SYNC_TOKEN_KEY, syncToken);
      pullState();
    });

    // Auto-sync events
    window.addEventListener("focus",   pullState);
    window.addEventListener("online",  pullState);

    // First pull on page load.
    if (configured()) {
      pullState();
    } else {
      setStatus("off");
    }
  })();
