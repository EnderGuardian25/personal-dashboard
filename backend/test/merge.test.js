import test from "node:test";
import assert from "node:assert/strict";

import { mergeState } from "../src/worker.js";

test("R-1: queue union — merged queue contains items unique to both existing and incoming", () => {
  const existing = {
    queue: [{ url: "A", title: "A title", src: "", done: false }],
    learning: {},
    track: "all",
  };
  const incoming = {
    queue: [{ url: "B", title: "B title", src: "", done: false }],
    learning: {},
    track: "all",
  };

  const merged = mergeState(existing, incoming);
  const urls = merged.queue.map((q) => q.url);

  assert.ok(urls.includes("A"), "merged queue should still contain A");
  assert.ok(urls.includes("B"), "merged queue should contain B from incoming");
});

test("R-2: done wins — incoming done:true overrides existing done:false for the same url, with no duplicate", () => {
  const existing = {
    queue: [{ url: "A", title: "A title", src: "", done: false }],
    learning: {},
    track: "all",
  };
  const incoming = {
    queue: [{ url: "A", title: "A title", src: "", done: true }],
    learning: {},
    track: "all",
  };

  const merged = mergeState(existing, incoming);
  const aItems = merged.queue.filter((q) => q.url === "A");

  assert.equal(aItems.length, 1, "merged queue should have exactly one item for url A");
  assert.equal(aItems[0].done, true, "done should win as true");
});

test("R-2 reverse: done wins — existing done:true is preserved even when incoming has done:false for the same url", () => {
  const existing = {
    queue: [{ url: "A", title: "A title", src: "", done: true }],
    learning: {},
    track: "all",
  };
  const incoming = {
    queue: [{ url: "A", title: "A title", src: "", done: false }],
    learning: {},
    track: "all",
  };

  const merged = mergeState(existing, incoming);
  const aItems = merged.queue.filter((q) => q.url === "A");

  assert.equal(aItems.length, 1, "merged queue should have exactly one item for url A");
  assert.equal(aItems[0].done, true, "done should stay true (done wins over false)");
});

test("R-3: learning is OR-merged per key and track takes the incoming value", () => {
  const existing = {
    queue: [],
    learning: { "learn-1": true },
    track: "cyber",
  };
  const incoming = {
    queue: [],
    learning: { "learn-1": false, "learn-2": true },
    track: "design",
  };

  const merged = mergeState(existing, incoming);

  assert.deepEqual(merged.learning, { "learn-1": true, "learn-2": true });
  assert.equal(merged.track, "design");
});
