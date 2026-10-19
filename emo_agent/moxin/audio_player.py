"""Build the single audio component used by the original conversation demo."""

import base64
import hashlib
import json
from pathlib import Path


def _track(data: str, version: int, name: str = ""):
    if not data:
        return None
    header = base64.b64decode(data[:64])
    mime = "audio/wav" if header.startswith(b"RIFF") else "audio/ogg" if header.startswith(b"OggS") else "audio/mpeg"
    return {"id": f"{version}:{hashlib.sha256(data.encode()).hexdigest()[:16]}", "src": f"data:{mime};base64,{data}", "name": name}


def player_html(music: str, music_name: str, music_version: int, speech: str, speech_version: int) -> str:
    config = json.dumps({"music": _track(music, music_version, music_name), "speech": _track(speech, speech_version)}, ensure_ascii=True).replace("</", "<\\/")
    script = Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
    return """<style>
      body{margin:0;color:#dbeafe;font:13px sans-serif;background:transparent}
      button{padding:6px 10px;margin:0 8px 5px 0;border-radius:6px;cursor:pointer}
      #track{font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      </style><button id="music">关闭背景音乐</button><button id="speech">重播朗读</button>
      <span id="status"></span><div id="track"></div><script>""" + script + "\n" + """
      const config = """ + config + """;
      const host = window.parent;
      const player = host.__moxinAudioController || (host.__moxinAudioController = MoxinAudio.createController(host));
      function render(state) {
        document.getElementById('music').textContent = state.enabled && !state.blocked && !state.suspended ? '关闭背景音乐' : '播放背景音乐';
        document.getElementById('music').disabled = !state.hasMusic;
        document.getElementById('speech').disabled = !state.hasSpeech;
        document.getElementById('track').textContent = state.musicName ? '当前背景音乐：' + state.musicName : '暂无背景音乐';
        document.getElementById('status').textContent = state.speaking ? '朗读中，背景音乐已暂停' : state.blocked ? '点击按钮开始播放' : '';
      }
      player.update(window, config, render);
      document.getElementById('music').onclick = () => player.toggleMusic();
      document.getElementById('speech').onclick = () => player.replaySpeech();
      window.addEventListener('pagehide', () => player.detach(window));
      window.addEventListener('unload', () => player.detach(window));
      </script>"""
