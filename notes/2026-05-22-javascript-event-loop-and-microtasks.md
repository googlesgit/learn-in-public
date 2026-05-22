# JavaScript event loop and microtasks

**Date:** 2026-05-22  
**Track:** Day A — Learn in public  
**Status:** Draft — review before merge

---

## What I learned

JavaScript runs **one call stack** on a single thread. The **event loop** decides what runs next when the stack is empty: it drains the **microtask queue** first, then takes one **macrotask** (timer, I/O callback, etc.), and repeats.

### Call stack vs queues

| Piece | What runs here |
|--------|----------------|
| **Call stack** | Your synchronous code — functions calling functions |
| **Microtask queue** | `Promise.then`, `queueMicrotask`, `MutationObserver` |
| **Macrotask queue** | `setTimeout`, `setInterval`, I/O, `setImmediate` (Node) |

Order after synchronous code finishes:

1. Run **all** pending microtasks (can enqueue more microtasks — those run too before moving on).
2. Run **one** macrotask.
3. Back to step 1.

So a `Promise.then` runs **before** a `setTimeout(0)` that was scheduled in the same synchronous block.

### Why microtasks exist

Promises need to resolve “soon” and in order relative to other promises, without waiting for the next timer tick. That keeps async/await predictable: code after `await` is scheduled as microtasks.

### `async` / `await

`await` pauses the **async function** and schedules the rest as microtasks when the promise settles. Other synchronous code on the stack still finishes first.

---

## Why it matters

- Explains “why did this log before that?” in React effects, fetch callbacks, and tests.
- Prevents bugs when you assume `setTimeout(fn, 0)` runs right after `promise.then(fn)` — it does not; the microtask wins.
- Node and browsers share this model (minor differences for `setImmediate` and I/O ordering in Node).

---

## Minimal example

See `examples/2026-05-22-event-loop-microtasks-demo.js`.

```bash
node examples/2026-05-22-event-loop-microtasks-demo.js
```

Expected order: `sync start` → `promise` → `microtask` → `timeout` → `sync end`.

---

## Gotcha / common mistake

**Starving the loop with infinite microtasks** — if each `Promise.then` schedules another, macrotasks (UI paint, timers) never run. Same class of bug: recursive `queueMicrotask` without yielding.

**Assuming `setTimeout(0)` means “run next”** — it means “run after current stack **and** all microtasks.” For “run after this promise chain,” use `queueMicrotask` or another promise.

---

## Further reading

- [Event loop (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Event_loop)
- [In depth: microtasks and the JavaScript runtime environment](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide/In_depth)
- [WHATWG HTML — event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)

---

## My review notes

**2-minute summary:** One thread, one stack. When sync code ends, **all microtasks** (promises) run, then **one timer/I/O task**. That’s why `Promise.then` beats `setTimeout(0)`.
