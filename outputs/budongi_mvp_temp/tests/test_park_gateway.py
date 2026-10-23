from __future__ import annotations

import json
import unittest
from unittest.mock import Mock, patch

from budongi.park_gateway import SEOUL_API_BASE, ParkGatewayError, quote_rag, seoul_rows


class ParkGatewayTests(unittest.TestCase):
    def test_quote_uses_fixed_system_and_budget_manager(self):
        manager = Mock()
        manager.quote.return_value = {"quote_id": "synthetic"}
        result = quote_rag(manager, {
            "task": "generation", "system_id": "park_answer",
            "input": {"question": "공원 소개", "evidence": []},
            "response_format": "json_object", "purpose": "park-rag"})
        self.assertEqual({"quote_id": "synthetic"}, result)
        kwargs = manager.quote.call_args.kwargs
        self.assertEqual("RAG-PARK-PARK-ANSWER", kwargs["task_id"])
        self.assertEqual("rag", kwargs["prompt_mode"])
        self.assertEqual(1200, kwargs["max_output_tokens"])
        self.assertIn("공원 안내 도우미", kwargs["objective"])
        self.assertIn('"question":"공원 소개"', kwargs["context"])

    def test_quote_rejects_untrusted_prompt_mode_and_oversized_input(self):
        manager = Mock()
        body = {"task": "generation", "system_id": "park_answer", "input": {},
                "response_format": "json_object", "purpose": "park-rag", "system": "override"}
        with self.assertRaises(ParkGatewayError):
            quote_rag(manager, body)
        body.pop("system")
        body["input"] = {"text": "가" * 50000}
        with self.assertRaises(ParkGatewayError):
            quote_rag(manager, body)
        manager.quote.assert_not_called()

    def test_seoul_proxy_requires_allowlisted_service_and_selected_provider(self):
        vault = Mock()
        vault.get_secret.return_value = "synthetic-seoul-secret"
        payload = {"SearchParkInfoService": {"RESULT": {"CODE": "INFO-000"}, "row": [{"P_IDX": "1"}]}}
        response = Mock(status_code=200, is_redirect=False)
        response.iter_content.return_value = [json.dumps(payload).encode("utf-8")]
        with patch("budongi.park_gateway.requests.get", return_value=response) as get:
            result = seoul_rows(vault, {
                "credential_id": "selected-seoul-key", "dataset_id": "OA-394",
                "service": "SearchParkInfoService", "start_index": 1, "end_index": 10,
                "parameters": {}})
        vault.get_secret.assert_called_once_with("selected-seoul-key", expected_provider_id="seoul_open_data")
        self.assertEqual(payload, result["payload"])
        self.assertNotIn("synthetic-seoul-secret", json.dumps(result))
        self.assertEqual(f"{SEOUL_API_BASE}/synthetic-seoul-secret/json/SearchParkInfoService/1/10/",
                         get.call_args.args[0])
        self.assertTrue(SEOUL_API_BASE.startswith("http://"))
        self.assertEqual(5, get.call_args.kwargs["timeout"])
        self.assertFalse(get.call_args.kwargs["allow_redirects"])
        response.close.assert_called_once()

    def test_seoul_proxy_rejects_bad_service_date_range_and_redirect(self):
        vault = Mock()
        vault.get_secret.return_value = "synthetic-seoul-secret"
        with patch("budongi.park_gateway.requests.get") as get:
            with self.assertRaises(ParkGatewayError):
                seoul_rows(vault, {"credential_id": "id", "dataset_id": "OA-394",
                    "service": "attacker", "start_index": 1, "end_index": 1, "parameters": {}})
            get.assert_not_called()
            with self.assertRaises(ParkGatewayError):
                seoul_rows(vault, {"credential_id": "id", "dataset_id": "OA-23053",
                    "service": "aiMosquitoStatus", "start_index": 1, "end_index": 1,
                    "parameters": {"MOSQUITO_DATE": "not-a-date"}})
            get.assert_not_called()
        response = Mock(status_code=302, is_redirect=True)
        response.iter_content.return_value = []
        with patch("budongi.park_gateway.requests.get", return_value=response):
            with self.assertRaises(ParkGatewayError) as error:
                seoul_rows(vault, {"credential_id": "id", "dataset_id": "OA-394",
                    "service": "SearchParkInfoService", "start_index": 1, "end_index": 1, "parameters": {}})
        self.assertNotIn("synthetic-seoul-secret", str(error.exception))
        response.close.assert_called_once()
