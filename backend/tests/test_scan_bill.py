"""
test_scan_bill.py — Receipt/bill parsing endpoint tests.

Tests that /scan-bill:
  1. Returns parsed data when Gemini Vision succeeds (mocked)
  2. Returns a graceful fallback (not a 500 crash) when Gemini raises an exception
  3. Returns a graceful fallback when the uploaded file is not a valid image
"""

import pytest
import io
from unittest.mock import patch, MagicMock
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image_upload(content: bytes, filename: str = "receipt.jpg", content_type: str = "image/jpeg"):
    """Build a multipart file upload for the test client."""
    return ("file", (filename, io.BytesIO(content), content_type))


def _make_mock_gemini_client(response_text: str):
    """Build a patched genai.Client that returns the given response text."""
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_instance.models.generate_content.return_value = mock_response
    return MagicMock(return_value=mock_instance)


# A minimal valid JPEG header (1×1 pixel white JPEG) so PIL doesn't reject it.
# Generated with: from PIL import Image; img=Image.new("RGB",(1,1)); buf=io.BytesIO(); img.save(buf,"JPEG")
TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=8"
    b"\x83&1=82<.342\x1edL\x85EICm\x8a\x8e\x8f\x95\xa2\x98\x90\x87"
    b"\xa2\x89\x90\x8d\x8c\x8c\x8f\x8f\x8f\x91\x8e\x8e\x91\x91\x91"
    b"\x8f\x90\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11"
    b"\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07"
    b"\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xce\xd6"
    b"\xff\xd9"
)


class TestScanBillEndpoint:
    def test_scan_bill_success_mocked(self, client):
        """
        When Gemini Vision returns valid JSON with amount/category/date,
        the endpoint parses and returns those fields correctly.
        """
        gemini_json = '{"amount": 450.0, "category": "Food", "date": "2024-06-15"}'
        mock_client_class = _make_mock_gemini_client(gemini_json)

        with patch("backend.api.genai.Client", mock_client_class), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
            resp = client.post(
                "/scan-bill",
                files=[_make_image_upload(TINY_JPEG)],
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["amount"] == 450.0
        assert body["category"] == "Food"
        assert body["date"] == "2024-06-15"

    def test_scan_bill_gemini_exception_graceful(self, client):
        """
        When the Gemini Vision call raises an exception, the endpoint must
        return 200 with a safe fallback — NOT a 500 server crash.
        """
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("Gemini API timeout")
        mock_client_class = MagicMock(return_value=mock_instance)

        with patch("backend.api.genai.Client", mock_client_class), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
            resp = client.post(
                "/scan-bill",
                files=[_make_image_upload(TINY_JPEG)],
            )

        assert resp.status_code == 200
        body = resp.json()
        # Graceful fallback values
        assert body["amount"] == 0
        assert body["category"] == "Extraction Failed"
        assert "date" in body  # date field must always be present

    def test_scan_bill_missing_api_key_graceful(self, client):
        """
        When GEMINI_API_KEY is absent, the endpoint returns early with a safe
        error response — no crash, no KeyError.
        """
        import os
        env_without_key = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}

        with patch.dict("os.environ", env_without_key, clear=True):
            resp = client.post(
                "/scan-bill",
                files=[_make_image_upload(TINY_JPEG)],
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "GEMINI_API_KEY" in body.get("category", "") or body["amount"] == 0

    def test_scan_bill_malformed_file_graceful(self, client):
        """
        Sending a plain text file (not a valid image) causes PIL.Image.open()
        to raise. The endpoint catches this and returns a safe fallback — not a 500.
        The fix is applied in api.py: Image.open() is now wrapped in try/except.
        """
        garbage = b"this is not an image file at all --- random bytes"
        mock_client_class = _make_mock_gemini_client('{"amount": 0}')

        with patch("backend.api.genai.Client", mock_client_class), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
            resp = client.post(
                "/scan-bill",
                files=[_make_image_upload(garbage, filename="notanimage.txt", content_type="text/plain")],
            )

        # Endpoint must return 200 with graceful fallback, not 500.
        assert resp.status_code == 200
        body = resp.json()
        assert "amount" in body
        assert "category" in body
        assert body["amount"] == 0  # Fallback value
        assert body["category"] == "Extraction Failed"
