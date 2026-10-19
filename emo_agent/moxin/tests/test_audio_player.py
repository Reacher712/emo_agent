import base64
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_player import player_html
import demo_frontend


class AudioComponentTests(unittest.TestCase):
    def test_generated_wav_and_new_tts_mp3_use_correct_media_types(self):
        music = base64.b64encode(b"RIFF0000WAVE" + b"0" * 40).decode()
        speech = base64.b64encode(b"ID3" + b"0" * 40).decode()
        html = player_html(music, "music", 1, speech, 1)
        self.assertIn("data:audio/wav;base64,", html)
        self.assertIn("data:audio/mpeg;base64,", html)
        self.assertNotIn("<audio", html)

    def test_empty_state_is_still_rendered_to_clear_previous_audio(self):
        html = player_html("", "", 1, "", 1)
        self.assertIn('"music": null', html)
        self.assertIn('"speech": null', html)
        self.assertIn("player.update(window, config, render)", html)

    def test_demo_renders_one_component_and_disabling_speech_clears_its_source(self):
        speech = base64.b64encode(b"ID3" + b"0" * 40).decode()
        with patch.object(demo_frontend.st, "session_state", {"reply_audio_b64": speech}), patch.object(demo_frontend.components, "html") as component:
            demo_frontend._render_audio_player(speech_enabled=False)
            component.assert_called_once()
            self.assertIn('"speech": null', component.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
