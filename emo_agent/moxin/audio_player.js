/* One music channel and one speech channel per page, retained across iframe rerenders. */
(function (root) {
  function createController(host) {
    const music = new host.Audio();
    const speech = new host.Audio();
    music.loop = true;
    music.volume = 0.35;
    speech.volume = 1;
    let owner = null, notify = null, musicId = null, speechId = null;
    let musicName = "", enabled = true, speaking = false, suspended = false, blocked = false;
    const tabId = Math.random().toString(36).slice(2);
    const channel = host.BroadcastChannel ? new host.BroadcastChannel("moxin-playback") : null;
    const snapshot = () => ({ musicName, enabled, speaking, blocked, suspended, hasMusic: !!musicId, hasSpeech: !!speechId });
    function changed() { if (notify) notify(snapshot()); }
    function claim() {
      suspended = false;
      if (channel) channel.postMessage({ type: "claim", tabId });
    }
    function playMusic() {
      if (!owner || !musicId || !enabled || speaking || suspended || !music.paused) return;
      music.play().then(() => { blocked = false; changed(); }).catch(() => { blocked = true; changed(); });
    }
    function playSpeech(reset) {
      if (!owner || !speechId || suspended) return;
      music.pause();
      speaking = true;
      if (reset) speech.currentTime = 0;
      if (!speech.paused) return;
      const id = speechId;
      speech.play().catch(() => {
        if (speechId !== id) return;
        speaking = false;
        blocked = true;
        playMusic();
        changed();
      });
    }
    speech.onended = () => { if (!speech.ended) return; speaking = false; playMusic(); changed(); };
    speech.onerror = () => { speaking = false; playMusic(); changed(); };
    if (channel) channel.onmessage = event => {
      if (!event.data || event.data.type !== "claim" || event.data.tabId === tabId) return;
      suspended = true;
      speaking = false;
      music.pause();
      speech.pause();
      changed();
    };
    function setSource(audio, source) {
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      if (source) audio.src = source;
    }
    return {
      update(frame, config, callback) {
        owner = frame;
        notify = callback;
        const nextMusic = config.music && config.music.id;
        const nextSpeech = config.speech && config.speech.id;
        const newMusic = (nextMusic || null) !== musicId;
        const newSpeech = (nextSpeech || null) !== speechId;
        if (newMusic) {
          musicId = nextMusic || null;
          musicName = config.music ? config.music.name : "";
          setSource(music, config.music && config.music.src);
        }
        if (newSpeech) {
          speechId = nextSpeech || null;
          speaking = false;
          setSource(speech, config.speech && config.speech.src);
        }
        if (newSpeech && speechId) {
          if (host.document.visibilityState !== "hidden") { claim(); playSpeech(true); }
          else suspended = true;
        } else if (speaking) {
          playSpeech(false);
        } else {
          if (newMusic && musicId) {
            if (host.document.visibilityState !== "hidden") claim();
            else suspended = true;
          }
          playMusic();
        }
        changed();
      },
      toggleMusic() {
        enabled = suspended || blocked ? true : !enabled;
        if (!enabled) music.pause();
        else { claim(); playMusic(); }
        changed();
      },
      replaySpeech() { claim(); playSpeech(true); changed(); },
      detach(frame) {
        if (owner !== frame) return;
        owner = null;
        notify = null;
        music.pause();
        speech.pause();
      },
      snapshot,
    };
  }
  if (typeof module !== "undefined" && module.exports) module.exports = { createController };
  else root.MoxinAudio = { createController };
})(typeof window !== "undefined" ? window : globalThis);
