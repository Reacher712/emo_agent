"""Regression checks for offline generation and truthful pipeline status."""

import base64
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_pipeline as pipeline


class LocalRuntimeTests(unittest.TestCase):
    def test_music_prompt_matches_requested_duration_override(self):
        emotion = {"emotion_label": "平静", "music_profile": {"style": "piano", "duration_sec": 180}}
        prompt = pipeline._render_music_prompt(emotion, {}, duration_sec=30)
        self.assertIn("30秒", prompt)
        self.assertNotIn("180秒", prompt)

    def test_image_metadata_preserves_actual_backend_seed(self):
        response = Mock()
        response.json.return_value = {
            "images": [base64.b64encode(b"test-image-bytes").decode()],
            "info": json.dumps({"seed": 777, "sd_model_hash": "model-hash"}),
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(pipeline.requests, "post", return_value=response) as post:
            image = Path(tmp) / "image.png"
            metadata = pipeline._sd_txt2img("http://127.0.0.1:7860", "ink", "noise", 768, 768, 12, 6.0, image, seed=42)
            self.assertEqual(metadata["actual_info"]["seed"], 777)
            self.assertEqual(post.call_args.kwargs["json"]["seed"], 42)
            self.assertTrue(image.with_suffix(".metadata.json").exists())

    def run_local(self, tmp):
        argv = ["run_pipeline.py", "--text", "local check", "--skip-music", "--output-dir", str(Path(tmp) / "images"), "--log-csv", str(Path(tmp) / "log.csv")]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
            pipeline.main()
        return json.loads(output.getvalue())

    def test_skip_music_does_not_call_cloud_service(self):
        emotion = {"emotion_label": "平静", "intensity": 2, "music_profile": {"duration_sec": "unused in local mode"}}
        template = {"id": "mock", "positive_prompt": "ink", "negative_prompt": "noise"}
        with tempfile.TemporaryDirectory() as tmp, patch.object(pipeline, "_load_env"), patch.object(pipeline, "infer_emotion", return_value=emotion), patch.object(pipeline, "select_template", return_value=template), patch.object(pipeline, "_sd_txt2img") as image, patch.object(pipeline, "_music_submit_and_query") as music:
            result = self.run_local(tmp)
            image.assert_called_once()
            self.assertEqual(image.call_args.kwargs["seed"], -1)
            music.assert_not_called()
            self.assertEqual(result["status"], "success")
            self.assertTrue(result["music_skipped"])

    def test_inference_failure_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(pipeline, "_load_env"), patch.object(pipeline, "infer_emotion", side_effect=RuntimeError("local model unavailable")), patch.object(pipeline, "_music_submit_and_query") as music:
            with self.assertRaises(SystemExit) as error:
                self.run_local(tmp)
            self.assertEqual(error.exception.code, 1)
            music.assert_not_called()


if __name__ == "__main__":
    unittest.main()
