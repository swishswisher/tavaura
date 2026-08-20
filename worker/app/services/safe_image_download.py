import asyncio
import http.client
import ipaddress
import logging
import socket
import ssl
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urljoin, urlsplit, urlunsplit

from PIL import Image, UnidentifiedImageError, features


CONNECT_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_WIDTH = 8192
MAX_IMAGE_HEIGHT = 8192
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_PORTS = {80, 443}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
if features.check("webp"):
    ALLOWED_CONTENT_TYPES.add("image/webp")

CONTENT_TYPE_FORMATS = {
    "image/jpeg": {"JPEG"},
    "image/png": {"PNG"},
    "image/webp": {"WEBP"},
}
LOGGER = logging.getLogger("tavaura.worker.safe_image_download")


class SafeImageDownloadError(RuntimeError):
    """Raised when remote media violates the worker intake policy."""


@dataclass(frozen=True)
class DownloadedImage:
    content: bytes
    content_type: str
    width: int
    height: int


@dataclass(frozen=True)
class _ValidatedTarget:
    url: str
    scheme: str
    hostname: str
    port: int
    request_target: str
    host_header: str
    addresses: tuple[str, ...]


class _PinnedHttpsConnection(http.client.HTTPSConnection):
    def __init__(self, target: _ValidatedTarget, address: str):
        super().__init__(
            host=target.hostname,
            port=target.port,
            timeout=CONNECT_TIMEOUT_SECONDS,
            context=ssl.create_default_context(),
        )
        self._validated_address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._validated_address, self.port),
            timeout=self.timeout,
        )
        raw_socket.settimeout(READ_TIMEOUT_SECONDS)
        self.sock = self._context.wrap_socket(
            raw_socket,
            server_hostname=self.host,
        )


async def download_image(image_url: str) -> DownloadedImage:
    return await asyncio.to_thread(download_image_sync, image_url)


def download_image_sync(image_url: str) -> DownloadedImage:
    current_url = image_url.strip() if image_url else ""
    for redirect_count in range(MAX_REDIRECTS + 1):
        target = _validate_target(current_url)
        status, headers, content = _request_target(target)

        if status in {301, 302, 303, 307, 308}:
            location = headers.get("location")
            if not location or redirect_count >= MAX_REDIRECTS:
                raise SafeImageDownloadError("Remote image redirect policy was exceeded.")
            current_url = urljoin(target.url, location)
            continue

        if status != 200:
            raise SafeImageDownloadError(f"Remote image returned HTTP {status}.")

        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise SafeImageDownloadError("Remote media is not an allowed image type.")

        width, height = _validate_image(content, content_type)
        LOGGER.info(
            "Accepted remote image: origin=%s status=%s content_type=%s byte_size=%s dimensions=%sx%s",
            _safe_origin(target.url),
            status,
            content_type,
            len(content),
            width,
            height,
        )
        return DownloadedImage(
            content=content,
            content_type=content_type,
            width=width,
            height=height,
        )

    raise SafeImageDownloadError("Remote image redirect policy was exceeded.")


def _validate_target(url: str) -> _ValidatedTarget:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise SafeImageDownloadError("Remote image URL is invalid.") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise SafeImageDownloadError("Remote image URL must use HTTP or HTTPS.")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise SafeImageDownloadError("Remote image URL host is invalid.")

    hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii")
    port = port or (443 if scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise SafeImageDownloadError("Remote image URL uses a disallowed port.")

    addresses = _resolve_public_addresses(hostname, port)
    path = parsed.path or "/"
    request_target = f"{path}?{parsed.query}" if parsed.query else path
    default_port = 443 if scheme == "https" else 80
    host_header = hostname if port == default_port else f"{hostname}:{port}"
    normalized_url = urlunsplit((scheme, host_header, path, parsed.query, ""))
    return _ValidatedTarget(
        url=normalized_url,
        scheme=scheme,
        hostname=hostname,
        port=port,
        request_target=request_target,
        host_header=host_header,
        addresses=addresses,
    )


def _resolve_public_addresses(hostname: str, port: int) -> tuple[str, ...]:
    try:
        records = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SafeImageDownloadError("Remote image host could not be resolved.") from exc

    addresses = tuple(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise SafeImageDownloadError("Remote image host did not resolve to an address.")
    _require_public_addresses(addresses)
    return addresses


def _require_public_addresses(addresses: tuple[str, ...]) -> None:
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise SafeImageDownloadError("Remote image host resolved unexpectedly.") from exc

        if (
            not ip.is_global
            or ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise SafeImageDownloadError("Remote image host resolves to a non-public address.")


def _request_target(target: _ValidatedTarget) -> tuple[int, dict[str, str], bytes]:
    last_error: Exception | None = None
    for address in target.addresses:
        connection: http.client.HTTPConnection
        if target.scheme == "https":
            connection = _PinnedHttpsConnection(target, address)
        else:
            connection = http.client.HTTPConnection(
                host=address,
                port=target.port,
                timeout=CONNECT_TIMEOUT_SECONDS,
            )

        try:
            connection.request(
                "GET",
                target.request_target,
                headers={
                    "Host": target.host_header,
                    "Accept": ", ".join(sorted(ALLOWED_CONTENT_TYPES)),
                    "User-Agent": "Tavaura-Media-Ingest/1.0",
                    "Connection": "close",
                },
            )
            if connection.sock is not None:
                connection.sock.settimeout(READ_TIMEOUT_SECONDS)
            response = connection.getresponse()
            headers = {name.lower(): value for name, value in response.getheaders()}
            content_length = headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > MAX_IMAGE_BYTES:
                        raise SafeImageDownloadError("Remote image exceeds the maximum byte size.")
                except ValueError as exc:
                    raise SafeImageDownloadError("Remote image Content-Length is invalid.") from exc

            content = _read_bounded(response)
            return response.status, headers, content
        except SafeImageDownloadError:
            raise
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
        finally:
            connection.close()

    raise SafeImageDownloadError("Remote image could not be downloaded safely.") from last_error


def _read_bounded(response: http.client.HTTPResponse) -> bytes:
    chunks: list[bytes] = []
    byte_count = 0
    while True:
        chunk = response.read(min(64 * 1024, MAX_IMAGE_BYTES + 1 - byte_count))
        if not chunk:
            break
        chunks.append(chunk)
        byte_count += len(chunk)
        if byte_count > MAX_IMAGE_BYTES:
            raise SafeImageDownloadError("Remote image exceeds the maximum byte size.")
    if byte_count == 0:
        raise SafeImageDownloadError("Remote image is empty.")
    return b"".join(chunks)


def _validate_image(content: bytes, content_type: str) -> tuple[int, int]:
    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            image_format = image.format
            if image_format not in CONTENT_TYPE_FORMATS[content_type]:
                raise SafeImageDownloadError("Remote image content does not match its MIME type.")
            if (
                width <= 0
                or height <= 0
                or width > MAX_IMAGE_WIDTH
                or height > MAX_IMAGE_HEIGHT
                or width * height > MAX_IMAGE_PIXELS
            ):
                raise SafeImageDownloadError("Remote image dimensions exceed the intake policy.")
            image.verify()
    except SafeImageDownloadError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise SafeImageDownloadError("Remote media is not a valid bounded image.") from exc
    return width, height


def _safe_origin(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
