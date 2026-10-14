#!/usr/bin/env python3
"""Restore the private CYPT reference decks used by the cypt-slide-template skill.

The two decks (Team Singapore "Magnetic Gear" and Team Slovakia "Wet Scroll") belong to other teams
and are NOT redistributed with the plugin. This tool downloads them from the sources recorded in
``skills/cypt-slide-template/references/local-references.manifest.json`` (or copies them from a local
backup), verifies each file's SHA-256 and byte size, and keeps only files that match the manifest.
Derived photos (``source-images/``) are then re-extracted from the Singapore deck.

Usage::

    python3 scripts/fetch_local_references.py --check                 # verify only, never writes
    python3 scripts/fetch_local_references.py                         # download missing decks
    python3 scripts/fetch_local_references.py --from-dir ~/Backups    # restore from a local folder

The default destination is ``<PT_RESEARCH_HOME>/local-references`` (``~/.config/pt-research`` unless
``PT_RESEARCH_HOME`` or ``PT_LOCAL_REFERENCES_DIR`` is set), which survives plugin updates.

Safety properties: files are written to a temporary file in the destination and renamed atomically
only after the size and SHA-256 match; a verified file is never overwritten; a mismatch is never kept.
Only the standard library is required (Pillow is optional, for PNG output of the derived photos).
Exit status: 0 when every deck is verified, 1 when a deck is missing or invalid, 2 on usage errors.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import http.cookiejar
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_paths  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PLUGIN_ROOT / "skills" / "cypt-slide-template" / "references" / "local-references.manifest.json"
USER_AGENT = "pt-research-fetch-local-references/1"
CHUNK = 1 << 16
MAX_HTML_BYTES = 2 * 1024 * 1024

OK = "ok"
MISSING = "missing"
SIZE_MISMATCH = "size-mismatch"
HASH_MISMATCH = "hash-mismatch"


class FetchError(Exception):
    """A recoverable problem with one source; the message is shown to the user."""


# --------------------------------------------------------------------------------------- verification

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file(path: Path, size: int, sha256: str) -> tuple[str, str]:
    """Return ``(status, detail)`` for ``path`` against the expected size and SHA-256."""

    try:
        actual_size = path.stat().st_size
    except OSError:
        return MISSING, "file not found"
    if not path.is_file():
        return MISSING, "not a regular file"
    if actual_size != size:
        return SIZE_MISMATCH, f"{actual_size} bytes, expected {size}"
    actual = sha256_file(path)
    if actual != sha256.lower():
        return HASH_MISMATCH, f"sha256 {actual}, expected {sha256.lower()}"
    return OK, f"{size} bytes, sha256 {sha256.lower()[:12]}..."


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FetchError(f"cannot read manifest {path}: {exc}")
    decks = data.get("decks")
    if not isinstance(decks, list) or not decks:
        raise FetchError(f"manifest {path} has no decks")
    for deck in decks:
        for key in ("filename", "sha256", "size", "source_url"):
            if key not in deck:
                raise FetchError(f"manifest deck is missing {key!r}: {deck}")
        name = deck["filename"]
        if Path(name).name != name or name in ("", ".", ".."):
            raise FetchError(f"manifest filename must be a plain file name: {name!r}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", str(deck["sha256"])):
            raise FetchError(f"manifest sha256 for {name} is not a SHA-256 hex digest")
    return data


# --------------------------------------------------------------------------------------- atomic placement

def _temp_in(directory: Path) -> tuple[int, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".fetch-", suffix=".part", dir=str(directory))
    return fd, Path(name)


def place_verified(temp: Path, final: Path, size: int, sha256: str, replace_invalid: bool) -> None:
    """Rename ``temp`` onto ``final`` only if it matches; otherwise delete it and raise."""

    status, detail = verify_file(temp, size, sha256)
    if status != OK:
        _unlink_quiet(temp)
        raise FetchError(f"rejected, {status} ({detail}); the file was discarded")
    existing, _ = verify_file(final, size, sha256)
    if existing == OK:
        _unlink_quiet(temp)
        return  # never overwrite a verified file
    if final.exists() and not replace_invalid:
        _unlink_quiet(temp)
        raise FetchError(f"{final.name} exists but does not match the manifest; re-run with --force to replace it")
    os.replace(temp, final)


def _unlink_quiet(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# --------------------------------------------------------------------------------------- local restore

def find_in_dir(directory: Path, filename: str) -> Optional[Path]:
    """Find ``filename`` directly inside ``directory`` (exact name first, then Unicode/case-insensitive)."""

    exact = directory / filename
    if exact.is_file():
        return exact
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return None
    wanted = unicodedata.normalize("NFC", filename).casefold()
    for name in names:
        if unicodedata.normalize("NFC", name).casefold() == wanted and (directory / name).is_file():
            return directory / name
    return None


def restore_from_dir(deck: dict, source_dir: Path, dest: Path, replace_invalid: bool = False) -> str:
    source = find_in_dir(source_dir, deck["filename"])
    if source is None:
        raise FetchError(f"{deck['filename']} not found in {source_dir}")
    status, detail = verify_file(source, int(deck["size"]), deck["sha256"])
    if status != OK:
        raise FetchError(f"{source} does not match the manifest ({status}: {detail}); not copied")
    dest.mkdir(parents=True, exist_ok=True)
    fd, temp = _temp_in(dest)
    os.close(fd)
    try:
        shutil.copyfile(source, temp)
        place_verified(temp, dest / deck["filename"], int(deck["size"]), deck["sha256"], replace_invalid)
    finally:
        _unlink_quiet(temp)
    return f"restored from {source}"


# --------------------------------------------------------------------------------------- download

def drive_confirm_url(page: str, base_url: str) -> Optional[str]:
    """Extract the follow-up URL from Google Drive's large-file / virus-scan interstitial page."""

    form = re.search(r"<form[^>]+action=[\"']([^\"']+)[\"'][^>]*>(.*?)</form>", page, re.S | re.I)
    if form:
        action = urllib.parse.urljoin(base_url, html.unescape(form.group(1)))
        params = []
        for tag in re.findall(r"<input[^>]*>", form.group(2), re.I):
            name = re.search(r"name=[\"']([^\"']*)[\"']", tag, re.I)
            value = re.search(r"value=[\"']([^\"']*)[\"']", tag, re.I)
            if name:
                params.append((html.unescape(name.group(1)), html.unescape(value.group(1)) if value else ""))
        if params:
            return action + ("&" if "?" in action else "?") + urllib.parse.urlencode(params)
    link = re.search(r"href=[\"']([^\"']*[?&;]confirm=[^\"']*)[\"']", page, re.I)
    if link:
        return urllib.parse.urljoin(base_url, html.unescape(link.group(1)))
    return None


def make_opener() -> urllib.request.OpenerDirector:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def _stream_to_file(response, temp: Path, limit: int) -> int:
    written = 0
    with open(temp, "wb") as handle:
        for block in iter(lambda: response.read(CHUNK), b""):
            written += len(block)
            if written > limit:
                raise FetchError(f"download is larger than the expected {limit} bytes; aborted")
            handle.write(block)
    return written


def download_to(url: str, temp: Path, expected_size: int, opener, timeout: float) -> None:
    """Download ``url`` into ``temp``, following Google Drive's confirmation page when one is served."""

    target = url
    for _attempt in range(3):
        try:
            response = opener.open(target, timeout=timeout)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise FetchError(f"{target.split('?')[0]}: {getattr(exc, 'reason', exc)}")
        with response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" not in content_type:
                _stream_to_file(response, temp, expected_size)
                return
            page = response.read(MAX_HTML_BYTES).decode("utf-8", "replace")
            base = response.geturl()
        follow = drive_confirm_url(page, base)
        if not follow or follow == target:
            raise FetchError("the server returned a web page instead of the file (quota exceeded, sign-in required or link removed)")
        target = follow
    raise FetchError("too many confirmation redirects")


def download_deck(deck: dict, dest: Path, opener, timeout: float, replace_invalid: bool = False) -> str:
    urls = [deck["source_url"]] + [u for u in deck.get("alternate_urls", []) if u != deck["source_url"]]
    errors = []
    dest.mkdir(parents=True, exist_ok=True)
    for url in urls:
        fd, temp = _temp_in(dest)
        os.close(fd)
        try:
            download_to(url, temp, int(deck["size"]), opener, timeout)
            place_verified(temp, dest / deck["filename"], int(deck["size"]), deck["sha256"], replace_invalid)
            return f"downloaded from {urllib.parse.urlsplit(url).netloc}"
        except FetchError as exc:
            errors.append(str(exc))
        finally:
            _unlink_quiet(temp)
    raise FetchError("; ".join(errors))


# --------------------------------------------------------------------------------------- derived photos (stdlib PDF reader)

_OBJ_RE = re.compile(rb"(?<![0-9])(\d+)[ \t]+(\d+)[ \t]+obj\b")


def iter_pdf_objects(data: bytes) -> Iterator[tuple[int, bytes, Optional[bytes]]]:
    """Yield ``(object number, dictionary/body bytes, stream bytes or None)`` for a PDF without compressed object streams."""

    pos = 0
    while True:
        match = _OBJ_RE.search(data, pos)
        if not match:
            return
        start = match.end()
        stream_at = data.find(b"stream", start)
        end_at = data.find(b"endobj", start)
        if stream_at != -1 and (end_at == -1 or stream_at < end_at):
            head = data[start:stream_at]
            body_start = stream_at + 6
            if data[body_start:body_start + 2] == b"\r\n":
                body_start += 2
            elif data[body_start:body_start + 1] in (b"\n", b"\r"):
                body_start += 1
            length = re.search(rb"/Length\s+(\d+)(?!\s+\d+\s+R)", head)
            body_end = -1
            if length:
                candidate = body_start + int(length.group(1))
                if data[candidate:candidate + 16].lstrip(b"\r\n ").startswith(b"endstream"):
                    body_end = candidate
            if body_end == -1:
                body_end = data.find(b"endstream", body_start)
                if body_end == -1:
                    return
            yield int(match.group(1)), head, data[body_start:body_end]
            end_obj = data.find(b"endobj", body_end)
            pos = (end_obj + 6) if end_obj != -1 else body_end + 9
        else:
            if end_at == -1:
                return
            yield int(match.group(1)), data[start:end_at], None
            pos = end_at + 6


def pdf_page_image_refs(data: bytes) -> list[list[tuple[str, int]]]:
    """Return, per page in reading order, the ``(XObject name, object number)`` pairs of that page's resources."""

    objects = {number: head for number, head, _stream in iter_pdf_objects(data)}

    def refs(blob: bytes, key: bytes) -> list[int]:
        found = re.search(key + rb"\s*\[(.*?)\]", blob, re.S)
        return [int(n) for n in re.findall(rb"(\d+)\s+\d+\s+R", found.group(1))] if found else []

    root = None
    for number, head in objects.items():
        if re.search(rb"/Type\s*/Catalog", head):
            found = re.search(rb"/Pages\s+(\d+)\s+\d+\s+R", head)
            if found:
                root = int(found.group(1))
                break
    if root is None:
        raise FetchError("PDF has no page tree")
    pages: list[int] = []

    def walk(number: int) -> None:
        head = objects.get(number, b"")
        if re.search(rb"/Type\s*/Pages", head):
            for kid in refs(head, rb"/Kids"):
                walk(kid)
        else:
            pages.append(number)

    walk(root)
    result: list[list[tuple[str, int]]] = []
    for number in pages:
        head = objects.get(number, b"")
        resources = head
        indirect = re.search(rb"/Resources\s+(\d+)\s+\d+\s+R", head)
        if indirect:
            resources = objects.get(int(indirect.group(1)), b"")
        xobject = re.search(rb"/XObject\s*(?:<<(.*?)>>|(\d+)\s+\d+\s+R)", resources, re.S)
        block = b""
        if xobject:
            block = xobject.group(1) if xobject.group(1) is not None else objects.get(int(xobject.group(2)), b"")
        result.append([(name.decode("latin-1"), int(num)) for name, num in re.findall(rb"/([^\s/<>\[\]()]+)\s+(\d+)\s+\d+\s+R", block)])
    return result


def extract_jpeg(data: bytes, page: int, xobject: str, width: int, height: int) -> bytes:
    """Return the raw JPEG (DCTDecode) stream of the named image XObject on a 1-based ``page``."""

    pages = pdf_page_image_refs(data)
    if not 1 <= page <= len(pages):
        raise FetchError(f"PDF has {len(pages)} pages; page {page} requested")
    number = dict(pages[page - 1]).get(xobject)
    if number is None:
        raise FetchError(f"page {page} has no image {xobject}")
    for candidate, head, stream in iter_pdf_objects(data):
        if candidate != number:
            continue
        if stream is None or not re.search(rb"/Subtype\s*/Image", head) or not re.search(rb"/DCTDecode", head):
            raise FetchError(f"{xobject} on page {page} is not a JPEG image")
        w = re.search(rb"/Width\s+(\d+)", head)
        h = re.search(rb"/Height\s+(\d+)", head)
        if not (w and h and int(w.group(1)) == width and int(h.group(1)) == height):
            raise FetchError(f"{xobject} on page {page} is not {width}x{height}")
        return stream
    raise FetchError(f"object {number} not found")


def regenerate_images(manifest: dict, dest: Path, force: bool, log: Callable[[str], None]) -> int:
    """Re-extract the derived photos from the verified Singapore deck. Returns the number of problems."""

    specs = manifest.get("derived_images", [])
    out_dir = dest / "source-images"
    problems = 0
    cache: dict[str, bytes] = {}
    try:
        from PIL import Image  # type: ignore
    except ImportError:  # pragma: no cover - depends on the environment
        Image = None  # type: ignore
        log("  note: Pillow is not installed; extracting the photos as .jpg (the builder accepts both). Install Pillow for PNG output.")
    for spec in specs:
        target_png = out_dir / spec["output"]
        target_jpg = target_png.with_suffix(".jpg")
        if (target_png.exists() or target_jpg.exists()) and not force:
            log(f"  {spec['output']}: already present")
            continue
        try:
            deck = dest / spec["source_deck"]
            if spec["source_deck"] not in cache:
                cache[spec["source_deck"]] = deck.read_bytes()
            jpeg = extract_jpeg(cache[spec["source_deck"]], int(spec["page"]), spec["xobject"], int(spec["width"]), int(spec["height"]))
            digest = hashlib.sha256(jpeg).hexdigest()
            if digest != spec["jpeg_sha256"]:
                raise FetchError(f"extracted JPEG sha256 {digest[:12]}... does not match the manifest")
            out_dir.mkdir(parents=True, exist_ok=True)
            if Image is not None:
                buffer = io.BytesIO()
                Image.open(io.BytesIO(jpeg)).convert("RGB").save(buffer, "PNG")
                payload, target = buffer.getvalue(), target_png
            else:
                payload, target = jpeg, target_jpg
            fd, temp = _temp_in(out_dir)
            os.close(fd)
            try:
                Path(temp).write_bytes(payload)
                os.replace(temp, target)
            finally:
                _unlink_quiet(Path(temp))
            log(f"  {target.name}: extracted (page {spec['page']}, {spec['width']}x{spec['height']})")
        except (FetchError, OSError) as exc:
            problems += 1
            log(f"  {spec['output']}: FAILED ({exc})")
    return problems


def report_images(manifest: dict, dest: Path, log: Callable[[str], None]) -> int:
    missing = 0
    for spec in manifest.get("derived_images", []):
        base = dest / "source-images" / spec["output"]
        if base.exists() or base.with_suffix(".jpg").exists():
            log(f"  {spec['output']}: present")
        else:
            missing += 1
            log(f"  {spec['output']}: missing")
    return missing


# --------------------------------------------------------------------------------------- command line

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore and verify the private CYPT reference decks (not redistributed with the plugin).",
    )
    parser.add_argument("--dest", type=Path, help="destination folder (default: <PT_RESEARCH_HOME>/local-references)")
    parser.add_argument("--from-dir", type=Path, metavar="DIR", help="restore from this local backup folder instead of downloading")
    parser.add_argument("--check", action="store_true", help="only verify what is present; write nothing")
    parser.add_argument("--force", action="store_true", help="replace an existing file that does not match the manifest (a verified file is never replaced)")
    parser.add_argument("--no-images", action="store_true", help="do not re-extract the derived photos in source-images/")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=60.0, help="network timeout in seconds (default 60)")
    return parser


def main(argv: Optional[list[str]] = None, opener=None, out=None) -> int:
    args = build_parser().parse_args(argv)
    stream = out or sys.stdout

    def log(message: str = "") -> None:
        print(message, file=stream)

    try:
        manifest = load_manifest(args.manifest)
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    dest = (args.dest.expanduser() if args.dest else local_paths.default_local_references_dir())
    log(f"Local references folder: {dest}")
    if args.check and args.from_dir:
        print("error: --check cannot be combined with --from-dir", file=sys.stderr)
        return 2

    failures = 0
    verified: set[str] = set()
    for deck in manifest["decks"]:
        name, size, digest = deck["filename"], int(deck["size"]), deck["sha256"]
        status, detail = verify_file(dest / name, size, digest)
        if status == OK:
            log(f"[ok]      {name}: verified ({detail})")
            verified.add(name)
            continue
        if args.check:
            log(f"[{status}] {name}: {detail}")
            failures += 1
            continue
        if status != MISSING and not args.force:
            log(f"[{status}] {name}: {detail}")
            log("          not replaced; investigate or re-run with --force to replace it")
            failures += 1
            continue
        try:
            if args.from_dir:
                note = restore_from_dir(deck, args.from_dir.expanduser(), dest, replace_invalid=args.force)
            else:
                note = download_deck(deck, dest, opener or make_opener(), args.timeout, replace_invalid=args.force)
            log(f"[ok]      {name}: {note}; verified sha256 and size")
            verified.add(name)
        except FetchError as exc:
            failures += 1
            log(f"[FAILED]  {name}: {exc}")

    image_problems = 0
    if manifest.get("derived_images"):
        log("Derived photos (source-images/):")
        sources = {spec["source_deck"] for spec in manifest["derived_images"]}
        if args.check:
            report_images(manifest, dest, log)
        elif args.no_images:
            log("  skipped (--no-images)")
        elif not sources <= verified:
            log("  skipped: the source deck is not verified yet")
        else:
            image_problems = regenerate_images(manifest, dest, args.force, log)

    if failures:
        log("")
        log("Next steps:")
        log("  - Re-run without --check to download, or pass --from-dir <backup folder> to restore from a local copy.")
        log("  - If downloads are blocked, fetch the files manually (exact file names, then re-run --check):")
        for deck in manifest["decks"]:
            if deck["filename"] not in verified:
                log(f"      {deck['filename']}  <-  {deck['source_url']}")
        log(f"  - Place them in: {dest}")
    else:
        log("")
        log("All reference decks are verified.")
        log("Next: make sure <PT_RESEARCH_HOME>/local.paths.json exists (see local.paths.example.json), then use the cypt-slide-template skill.")
        log("To rebuild the photo-embedded starter decks, see README.md section 'Restoring private CYPT reference decks'.")
    return 1 if failures or image_problems else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
