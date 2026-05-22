#!/usr/bin/env node
/**
 * Event loop order: sync → microtasks → macrotasks
 * Run: node examples/2026-05-22-event-loop-microtasks-demo.js
 */

console.log('1 sync start');

setTimeout(() => console.log('4 timeout (macrotask)'), 0);

Promise.resolve().then(() => console.log('3 promise (microtask)'));

queueMicrotask(() => console.log('3b queueMicrotask (microtask)'));

console.log('2 sync end');
