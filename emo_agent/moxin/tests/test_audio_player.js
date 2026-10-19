const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createController } = require('../audio_player.js');

function host(channels = []) {
  const audio = [];
  class FakeAudio {
    constructor() { this.paused = true; this.ended = false; this.currentTime = 0; this.plays = 0; audio.push(this); }
    play() { this.paused = false; this.ended = false; this.plays++; return Promise.resolve(); }
    pause() { this.paused = true; }
    removeAttribute() { this.src = ''; }
    load() { this.currentTime = 0; this.ended = false; }
    finish() { this.paused = true; this.ended = true; this.onended(); }
  }
  class FakeChannel {
    constructor() { channels.push(this); }
    postMessage(data) { for (const peer of channels) if (peer !== this && peer.onmessage) peer.onmessage({ data }); }
  }
  return { Audio: FakeAudio, BroadcastChannel: FakeChannel, document: { visibilityState: 'visible' }, audio };
}
const track = id => ({ id, src: `audio:${id}`, name: id });
const config = (music = 'old', speech = null) => ({ music: music ? track(music) : null, speech: speech ? track(speech) : null });

test('replacing a background reuses the only music channel and stops the previous source', () => {
  const h = host(), c = createController(h), frame = {};
  c.update(frame, config(), () => {});
  const music = h.audio[0];
  assert.equal(music.paused, false);
  c.update(frame, config('generated'), () => {});
  assert.equal(h.audio.length, 2);
  assert.equal(h.audio[0], music);
  assert.equal(music.src, 'audio:generated');
  assert.equal(music.currentTime, 0);
});

test('rerender does not restart the same background or replay completed speech', () => {
  const h = host(), c = createController(h);
  c.update({}, config('bg', 'reply'), () => {});
  h.audio[1].finish();
  h.audio[0].currentTime = 12;
  const counts = h.audio.map(a => a.plays);
  c.update({}, config('bg', 'reply'), () => {});
  assert.deepEqual(h.audio.map(a => a.plays), counts);
  assert.equal(h.audio[0].currentTime, 12);
});

test('speech pauses music, even when a new music track arrives, then resumes the new track', () => {
  const h = host(), c = createController(h);
  c.update({}, config(), () => {});
  c.update({}, config('old', 'reply'), () => {});
  assert.equal(h.audio[0].paused, true);
  assert.equal(h.audio[1].paused, false);
  c.update({}, config('new', 'reply'), () => {});
  assert.equal(h.audio[0].paused, true);
  h.audio[1].finish();
  assert.equal(h.audio[0].paused, false);
  assert.equal(h.audio[0].src, 'audio:new');
});

test('turning off background prevents automatic resumption after speech', () => {
  const h = host(), c = createController(h);
  c.update({}, config('bg', 'reply'), () => {});
  c.toggleMusic();
  h.audio[1].finish();
  assert.equal(h.audio[0].paused, true);
});

test('reset stops and releases both audio sources', () => {
  const h = host(), c = createController(h);
  c.update({}, config('bg', 'reply'), () => {});
  c.update({}, config(null, null), () => {});
  assert.ok(h.audio.every(a => a.paused && !a.src));
});

test('late unload of an old iframe cannot stop its replacement', () => {
  const h = host(), c = createController(h), oldFrame = {}, newFrame = {};
  c.update(oldFrame, config(), () => {});
  c.update(newFrame, config(), () => {});
  c.detach(oldFrame);
  assert.equal(h.audio[0].paused, false);
  c.detach(newFrame);
  assert.equal(h.audio[0].paused, true);
});

test('starting playback in another tab suspends old audio without rerender stealing it back', () => {
  const channels = [], first = host(channels), second = host(channels);
  const a = createController(first), b = createController(second);
  a.update({}, config('one'), () => {});
  b.update({}, config('two'), () => {});
  assert.equal(first.audio[0].paused, true);
  assert.equal(second.audio[0].paused, false);
  a.update({}, config('one'), () => {});
  assert.equal(first.audio[0].paused, true);
  a.toggleMusic();
  assert.equal(first.audio[0].paused, false);
  assert.equal(second.audio[0].paused, true);
});

test('an iframe replacement resumes ongoing speech without starting it over', () => {
  const h = host(), c = createController(h), frame = {};
  c.update(frame, config('bg', 'reply'), () => {});
  h.audio[1].currentTime = 4;
  c.detach(frame);
  c.update({}, config('bg', 'reply'), () => {});
  assert.equal(h.audio[1].paused, false);
  assert.equal(h.audio[1].currentTime, 4);
  assert.equal(h.audio[0].paused, true);
});

test('a blocked autoplay can be started with a single button click', async () => {
  const h = host(), c = createController(h);
  const originalPlay = h.audio[0].play;
  h.audio[0].play = () => Promise.reject(new Error('autoplay blocked'));
  c.update({}, config('bg'), () => {});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(c.snapshot().blocked, true);
  h.audio[0].play = originalPlay;
  c.toggleMusic();
  assert.equal(h.audio[0].paused, false);
  assert.equal(c.snapshot().enabled, true);
});
