import unittest
from unittest import mock

from reincrew import local_ai


class LocalPayloadTests(unittest.TestCase):
    def test_thinking_disabled_and_loopback_only(self):
        q = {"question": "What is a list?", "reference": "ordered collection", "concepts": {}}
        resp = mock.Mock()
        resp.json.return_value = {"response": '{"correctness_score":80,"knowledge_depth_score":70,"completeness_score":60}'}
        resp.raise_for_status.return_value = None
        with mock.patch("reincrew.local_ai.requests.post", return_value=resp) as post:
            out = local_ai.score_with_ollama(q, "an ordered collection", url="http://127.0.0.1:11434/api/generate", model="x")
        body = post.call_args.kwargs["json"]
        self.assertIs(body["think"], False)
        self.assertEqual(out["final_score"], round(80 * .6 + 70 * .25 + 60 * .15))
        with self.assertRaises(local_ai.NonLocalEndpointError):
            local_ai.score_with_ollama(q, "x", url="http://example.com/api/generate")

    def test_warm_up_never_raises(self):
        with mock.patch("reincrew.local_ai.requests.post", side_effect=RuntimeError("down")):
            local_ai.warm_up()


if __name__ == "__main__":
    unittest.main()
