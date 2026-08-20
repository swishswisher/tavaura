import socket
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image

from app.services import safe_image_download as safe_download


def _address_record(address: str):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sockaddr = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


class SafeImageDownloadPolicyTests(unittest.TestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "HTTP or HTTPS"):
            safe_download._validate_target("file:///etc/passwd")

    def test_rejects_credentials_and_nonstandard_ports(self):
        with self.assertRaises(safe_download.SafeImageDownloadError):
            safe_download._validate_target("https://user:secret@example.com/image.png")
        with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "disallowed port"):
            safe_download._validate_target("https://example.com:8443/image.png")

    def test_rejects_every_non_public_address_class(self):
        blocked = (
            "127.0.0.1",
            "10.0.0.1",
            "169.254.169.254",
            "224.0.0.1",
            "0.0.0.0",
            "192.0.2.1",
            "::1",
            "fc00::1",
            "fe80::1",
        )
        for address in blocked:
            with self.subTest(address=address):
                with self.assertRaisesRegex(
                    safe_download.SafeImageDownloadError,
                    "non-public address",
                ):
                    safe_download._require_public_addresses((address,))

    def test_rejects_mixed_public_and_private_dns_answers(self):
        with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "non-public address"):
            safe_download._require_public_addresses(("93.184.216.34", "127.0.0.1"))

    @patch.object(safe_download, "_request_target")
    @patch.object(safe_download.socket, "getaddrinfo")
    def test_redirect_target_is_resolved_and_revalidated(self, getaddrinfo, request_target):
        getaddrinfo.side_effect = [
            [_address_record("93.184.216.34")],
            [_address_record("127.0.0.1")],
        ]
        request_target.return_value = (
            302,
            {"location": "http://internal.example/private.png"},
            b"redirect",
        )

        with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "non-public address"):
            safe_download.download_image_sync("https://example.com/image.png")
        self.assertEqual(request_target.call_count, 1)

    def test_rejects_mime_content_mismatch(self):
        output = BytesIO()
        Image.new("RGB", (8, 8), "white").save(output, format="PNG")
        with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "MIME type"):
            safe_download._validate_image(output.getvalue(), "image/jpeg")

    def test_accepts_a_small_matching_image(self):
        output = BytesIO()
        Image.new("RGB", (12, 9), "white").save(output, format="PNG")
        self.assertEqual(
            safe_download._validate_image(output.getvalue(), "image/png"),
            (12, 9),
        )

    def test_rejects_oversized_content_length_before_reading(self):
        class FakeConnection:
            sock = None

            def request(self, *_args, **_kwargs):
                return None

            def getresponse(self):
                return FakeResponse()

            def close(self):
                return None

        class FakeResponse:
            status = 200

            def getheaders(self):
                return [("Content-Length", str(safe_download.MAX_IMAGE_BYTES + 1))]

        target = safe_download._ValidatedTarget(
            url="http://example.com/image.png",
            scheme="http",
            hostname="example.com",
            port=80,
            request_target="/image.png",
            host_header="example.com",
            addresses=("93.184.216.34",),
        )
        with patch.object(safe_download.http.client, "HTTPConnection", return_value=FakeConnection()):
            with self.assertRaisesRegex(safe_download.SafeImageDownloadError, "maximum byte size"):
                safe_download._request_target(target)


if __name__ == "__main__":
    unittest.main()
