import base64
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import doubao_voice as voice


def frame(data):
    return json.dumps(data).encode()


class VoiceV3Tests(unittest.TestCase):
    def test_combines_chunks_only_after_successful_completion(self):
        lines = [frame({"code": 0, "data": base64.b64encode(b"first").decode()}), frame({"code": 0, "data": base64.b64encode(b"second").decode()}), frame({"code": 20000000, "data": None})]
        self.assertEqual(voice.decode_v3_audio(lines), b"firstsecond")

    def test_interrupted_stream_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "未正常结束"):
            voice.decode_v3_audio([frame({"code": 0, "data": base64.b64encode(b"partial").decode()})])

    def test_permission_denial_is_not_success(self):
        with self.assertRaisesRegex(RuntimeError, "45000000"):
            voice.decode_v3_audio([frame({"code": 45000000, "message": "permission denied"})])

    def test_new_key_routes_without_legacy_credentials(self):
        with patch.object(voice, "_load_env"), patch.dict(voice.os.environ, {"TTS_API_KEY": "test-only", "TTS_V3_SPEAKER": "test-speaker"}, clear=True), patch.object(voice, "volc_tts_v3", return_value=(None, None)) as v3, patch.object(voice, "volc_tts") as legacy:
            voice.tts_with_voice("test")
            v3.assert_called_once_with("test", speaker="test-speaker", output_path=None)
            legacy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
