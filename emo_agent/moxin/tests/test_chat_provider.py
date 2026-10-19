from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import doubao_voice as voice


class ChatProviderTests(unittest.TestCase):
    def test_deepseek_uses_its_own_key_and_does_not_duplicate_current_message(self):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "test reply"}}]}
        settings = {"CHAT_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "test-deepseek", "DOUBAO_API_KEY": "test-ark"}
        with patch.object(voice, "_load_env"), patch.dict(voice.os.environ, settings, clear=True), patch.object(voice.requests, "post", return_value=response) as post:
            reply = voice.chat_reply("hello", history=[{"role": "user", "text": "hello"}])
            self.assertEqual(reply, "test reply")
            self.assertEqual(post.call_args.args[0], "https://api.deepseek.com/chat/completions")
            self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-deepseek")
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["model"], "deepseek-flash")
            self.assertEqual(payload["thinking"], {"type": "disabled"})
            self.assertEqual(sum(m["role"] == "user" for m in payload["messages"]), 1)

    def test_missing_deepseek_key_never_uses_ark_key(self):
        with patch.object(voice, "_load_env"), patch.dict(voice.os.environ, {"CHAT_PROVIDER": "deepseek", "DOUBAO_API_KEY": "test-ark"}, clear=True), patch.object(voice.requests, "post") as post:
            self.assertIsNone(voice.chat_reply("hello"))
            post.assert_not_called()

    def test_legacy_entry_still_explicitly_uses_doubao(self):
        with patch.object(voice, "chat_reply", return_value="reply") as chat:
            voice.doubao_chat("hello")
            self.assertEqual(chat.call_args.kwargs["provider"], "doubao")

    def test_failed_cloud_call_is_marked_as_local_fallback(self):
        with patch.object(voice, "chat_reply", return_value=None):
            reply = voice.get_reply_and_audio("hello", fallback_reply="local reply", use_tts=False)
            self.assertEqual(reply["text"], "local reply")
            self.assertTrue(reply["chat_fallback"])


if __name__ == "__main__":
    unittest.main()
