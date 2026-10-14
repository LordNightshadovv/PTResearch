"""Offline tests for the user-level private data directory and the reference-deck restore tool.

Nothing here touches the network or the real ``~/.config/pt-research``: every test builds its own
temporary HOME / PT_RESEARCH_HOME and a fake HTTP opener.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _isolated_home  # noqa: E402,F401  (never read the real ~/.config/pt-research)
import fetch_local_references as fetch  # noqa: E402
import local_paths  # noqa: E402
from validate_plugin import check_local_references_manifest  # noqa: E402

SKILL = ROOT / "skills" / "cypt-slide-template"
MANIFEST = SKILL / "references" / "local-references.manifest.json"
NODE = shutil.which("node")
PAYLOAD_A = b"%PDF-1.7 fake deck A\n" * 50
PAYLOAD_B = b"%PDF-1.7 fake deck B\n" * 70


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fake_manifest(payload_a: bytes = PAYLOAD_A, payload_b: bytes = PAYLOAD_B, derived: list | None = None) -> dict:
    return {
        "schema": "pt-research-local-references-manifest", "version": 1,
        "decks": [
            {"filename": "Deck A.pdf", "team": "Team A", "problem": "Problem A.", "size": len(payload_a), "sha256": sha(payload_a),
             "source_url": "https://example.invalid/a"},
            {"filename": "Deck B.pdf", "team": "Team B", "problem": "Problem B.", "size": len(payload_b), "sha256": sha(payload_b),
             "source_url": "https://example.invalid/b", "alternate_urls": ["https://example.invalid/b2"]},
        ],
        "derived_images": derived or [],
    }


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/pdf", url: str = "https://example.invalid/x") -> None:
        self._stream = io.BytesIO(body)
        self.headers = {"Content-Type": content_type}
        self._url = url

    def read(self, n: int = -1) -> bytes:
        return self._stream.read(n)

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc) -> None:
        return None


class FakeOpener:
    """Maps URL substrings to bodies; records every request. Unknown URLs fail like a dead network."""

    def __init__(self, routes: dict[str, object]) -> None:
        self.routes = routes
        self.requests: list[str] = []

    def open(self, url: str, timeout: float = 0):
        self.requests.append(url)
        for key, value in self.routes.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value() if callable(value) else FakeResponse(value)  # type: ignore[arg-type]
        raise fetch.urllib.error.URLError("network disabled in tests")


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="pt-localrefs-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.home = self.temp / "home" / "pt-research"
        patcher = mock.patch.dict(os.environ, {"PT_RESEARCH_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("PT_LOCAL_REFERENCES_DIR", None)
        self.manifest_path = self.temp / "manifest.json"

    def write_manifest(self, manifest: dict | None = None) -> Path:
        self.manifest_path.write_text(json.dumps(manifest or fake_manifest()), encoding="utf-8")
        return self.manifest_path

    def run_main(self, *args: str, opener=None) -> tuple[int, str]:
        out = io.StringIO()
        code = fetch.main(["--manifest", str(self.manifest_path), *args], opener=opener, out=out)
        return code, out.getvalue()

    def leftovers(self, folder: Path) -> list[str]:
        return sorted(p.name for p in folder.rglob("*.part")) if folder.exists() else []


class PythonResolutionOrderTests(TempDirCase):
    def setUp(self) -> None:
        super().setUp()
        self.root = self.temp / "plugin"
        self.root.mkdir()
        self.home.mkdir(parents=True)

    def test_key_order_env_then_home_then_plugin_json_then_env_file_then_default(self) -> None:
        (self.root / ".env.local").write_text("K=env-file\n", encoding="utf-8")
        self.assertEqual(local_paths.resolve("K", "d", self.root), "env-file")
        (self.root / "local.paths.json").write_text(json.dumps({"K": "plugin-json"}), encoding="utf-8")
        self.assertEqual(local_paths.resolve("K", "d", self.root), "plugin-json")
        (self.home / "local.paths.json").write_text(json.dumps({"K": "home-json"}), encoding="utf-8")
        self.assertEqual(local_paths.resolve("K", "d", self.root), "home-json")
        with mock.patch.dict(os.environ, {"K": "from-env"}):
            self.assertEqual(local_paths.resolve("K", "d", self.root), "from-env")
        self.assertEqual(local_paths.resolve("OTHER", "d", self.root), "d")

    def test_home_json_that_lacks_the_key_falls_through_to_the_plugin_copy(self) -> None:
        (self.home / "local.paths.json").write_text(json.dumps({"A": "1", "_comment": "x"}), encoding="utf-8")
        (self.root / "local.paths.json").write_text(json.dumps({"B": "2"}), encoding="utf-8")
        self.assertEqual(local_paths.resolve("B", None, self.root), "2")
        self.assertIsNone(local_paths.resolve("_comment", None, self.root))

    def test_default_home_is_dot_config_pt_research_under_the_user_home(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "PT_RESEARCH_HOME"}
        env["HOME"] = str(self.temp / "fake-user")
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(local_paths.research_home(), self.temp / "fake-user" / ".config" / "pt-research")

    def test_local_references_dir_order_and_explicit_override(self) -> None:
        plugin_refs = self.root / local_paths.PLUGIN_LOCAL_REFERENCES
        self.assertIsNone(local_paths.local_references_dir(self.root))
        plugin_refs.mkdir(parents=True)
        self.assertEqual(local_paths.local_references_dir(self.root), plugin_refs)
        (self.home / "local-references").mkdir()
        self.assertEqual(local_paths.local_references_dir(self.root), self.home / "local-references")
        explicit = self.temp / "explicit"
        with mock.patch.dict(os.environ, {"PT_LOCAL_REFERENCES_DIR": str(explicit)}):
            self.assertIsNone(local_paths.local_references_dir(self.root), "an explicit but missing folder is used exclusively")
            explicit.mkdir()
            self.assertEqual(local_paths.local_references_dir(self.root), explicit)
            self.assertEqual(local_paths.default_local_references_dir(), explicit)
        self.assertEqual(local_paths.default_local_references_dir(), self.home / "local-references")


@unittest.skipUnless(NODE, "node is unavailable")
class NodeParityTests(TempDirCase):
    """The template builder resolves settings through local_paths.mjs; it must agree with local_paths.py."""

    def setUp(self) -> None:
        super().setUp()
        self.root = self.temp / "plugin"
        (self.root / local_paths.PLUGIN_LOCAL_REFERENCES).mkdir(parents=True)
        self.home.mkdir(parents=True)
        self.script = SKILL / "scripts" / "local_paths.mjs"

    def node(self, *args: str, **env: str) -> str:
        full = {k: v for k, v in os.environ.items() if k not in ("PT_LOCAL_REFERENCES_DIR",)}
        full.update(env)
        result = subprocess.run([NODE, str(self.script), str(self.root), *args], capture_output=True, text=True, env=full, check=True)
        return result.stdout.strip()

    def test_setting_order_matches_python(self) -> None:
        (self.root / ".env.local").write_text("K=env-file\n", encoding="utf-8")
        (self.root / "local.paths.json").write_text(json.dumps({"K": "plugin-json"}), encoding="utf-8")
        (self.home / "local.paths.json").write_text(json.dumps({"K": "home-json", "_comment": "ignored"}), encoding="utf-8")
        self.assertEqual(self.node("setting", "K"), local_paths.resolve("K", None, self.root))
        self.assertEqual(self.node("setting", "K"), "home-json")
        self.assertEqual(self.node("setting", "K", K="from-env"), "from-env")
        (self.home / "local.paths.json").unlink()
        self.assertEqual(self.node("setting", "K"), "plugin-json")
        (self.root / "local.paths.json").unlink()
        self.assertEqual(self.node("setting", "K"), "env-file")
        self.assertEqual(self.node("setting", "_comment"), "")

    def test_reference_folder_order_matches_python(self) -> None:
        plugin_refs = self.root / local_paths.PLUGIN_LOCAL_REFERENCES
        self.assertEqual(self.node("refs"), str(local_paths.local_references_dir(self.root)))
        (self.home / "local-references").mkdir()
        self.assertEqual(self.node("refs"), str(self.home / "local-references"))
        self.assertNotEqual(self.node("refs"), str(plugin_refs))
        explicit = self.temp / "explicit"
        self.assertEqual(self.node("refs", PT_LOCAL_REFERENCES_DIR=str(explicit)), "")
        explicit.mkdir()
        self.assertEqual(self.node("refs", PT_LOCAL_REFERENCES_DIR=str(explicit)), str(explicit))

    def test_default_home_uses_the_user_home_directory(self) -> None:
        fake = self.temp / "fake-user"
        (fake / ".config" / "pt-research").mkdir(parents=True)
        (fake / ".config" / "pt-research" / "local.paths.json").write_text(json.dumps({"K": "default-home"}), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "PT_RESEARCH_HOME"}
        env["HOME"] = str(fake)
        result = subprocess.run([NODE, str(self.script), str(self.root), "setting", "K"], capture_output=True, text=True, env=env, check=True)
        self.assertEqual(result.stdout.strip(), "default-home")


class VerificationTests(TempDirCase):
    def test_statuses(self) -> None:
        path = self.temp / "f.bin"
        self.assertEqual(fetch.verify_file(path, 3, sha(b"abc"))[0], fetch.MISSING)
        path.write_bytes(b"abc")
        self.assertEqual(fetch.verify_file(path, 3, sha(b"abc"))[0], fetch.OK)
        self.assertEqual(fetch.verify_file(path, 3, sha(b"abc").upper())[0], fetch.OK)
        self.assertEqual(fetch.verify_file(path, 4, sha(b"abc"))[0], fetch.SIZE_MISMATCH)
        self.assertEqual(fetch.verify_file(path, 3, sha(b"abd"))[0], fetch.HASH_MISMATCH)

    def test_directory_is_not_a_file(self) -> None:
        self.assertEqual(fetch.verify_file(self.temp, 0, sha(b""))[0], fetch.MISSING)

    def test_find_in_dir_tolerates_case_and_unicode_form(self) -> None:
        (self.temp / "Café Deck.pdf").write_bytes(b"x")
        found = fetch.find_in_dir(self.temp, "cafe\u0301 deck.PDF")
        self.assertIsNotNone(found)
        self.assertTrue(found.is_file())  # type: ignore[union-attr]
        self.assertIsNone(fetch.find_in_dir(self.temp, "other.pdf"))

    def test_committed_manifest_is_valid_and_public_safe(self) -> None:
        self.assertEqual(check_local_references_manifest(ROOT), [])
        data = fetch.load_manifest(MANIFEST)
        self.assertEqual({d["filename"] for d in data["decks"]}, {"Magnetic Gear Singapore.pdf", "Wet Scroll Slovakia.pdf"})
        for deck in data["decks"]:
            self.assertRegex(deck["source_url"], r"^https://drive\.google\.com/uc\?export=download&id=[A-Za-z0-9_-]+$")
            self.assertGreater(deck["size"], 1_000_000)
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertNotIn("@", text)

    def test_manifest_loader_rejects_path_traversal_and_bad_hashes(self) -> None:
        bad = fake_manifest()
        bad["decks"][0]["filename"] = "../evil.pdf"
        self.write_manifest(bad)
        with self.assertRaises(fetch.FetchError):
            fetch.load_manifest(self.manifest_path)
        bad = fake_manifest()
        bad["decks"][0]["sha256"] = "xyz"
        self.write_manifest(bad)
        with self.assertRaises(fetch.FetchError):
            fetch.load_manifest(self.manifest_path)


class RestoreFromDirTests(TempDirCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_manifest()
        self.backup = self.temp / "backup"
        self.dest = self.temp / "dest"
        self.backup.mkdir()

    def test_restores_and_verifies_without_the_network(self) -> None:
        (self.backup / "Deck A.pdf").write_bytes(PAYLOAD_A)
        (self.backup / "deck b.PDF").write_bytes(PAYLOAD_B)
        opener = FakeOpener({})
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup), opener=opener)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.dest / "Deck A.pdf").read_bytes(), PAYLOAD_A)
        self.assertEqual((self.dest / "Deck B.pdf").read_bytes(), PAYLOAD_B)
        self.assertEqual(opener.requests, [])
        self.assertEqual(self.leftovers(self.dest), [])
        self.assertEqual(self.run_main("--dest", str(self.dest), "--check")[0], 0)

    def test_mismatching_backup_is_rejected_and_nothing_is_kept(self) -> None:
        (self.backup / "Deck A.pdf").write_bytes(PAYLOAD_A + b"tampered")
        (self.backup / "Deck B.pdf").write_bytes(PAYLOAD_B[:-1] + b"X")
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup))
        self.assertEqual(code, 1, out)
        self.assertIn("does not match the manifest", out)
        self.assertFalse((self.dest / "Deck A.pdf").exists())
        self.assertFalse((self.dest / "Deck B.pdf").exists())
        self.assertEqual(self.leftovers(self.dest), [])
        self.assertIn("Next steps", out)

    def test_missing_backup_file_is_reported_with_manual_links(self) -> None:
        (self.backup / "Deck A.pdf").write_bytes(PAYLOAD_A)
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup))
        self.assertEqual(code, 1, out)
        self.assertTrue((self.dest / "Deck A.pdf").is_file())
        self.assertIn("Deck B.pdf", out)
        self.assertIn("https://example.invalid/b", out)

    def test_verified_destination_file_is_never_overwritten(self) -> None:
        self.dest.mkdir()
        (self.dest / "Deck A.pdf").write_bytes(PAYLOAD_A)
        before = os.stat(self.dest / "Deck A.pdf")
        (self.backup / "Deck A.pdf").write_bytes(PAYLOAD_A)
        (self.backup / "Deck B.pdf").write_bytes(PAYLOAD_B)
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup), "--force")
        self.assertEqual(code, 0, out)
        self.assertEqual(os.stat(self.dest / "Deck A.pdf").st_ino, before.st_ino)
        self.assertIn("[ok]      Deck A.pdf: verified", out)

    def test_corrupt_destination_needs_force(self) -> None:
        self.dest.mkdir()
        (self.dest / "Deck A.pdf").write_bytes(b"corrupt")
        (self.backup / "Deck A.pdf").write_bytes(PAYLOAD_A)
        (self.backup / "Deck B.pdf").write_bytes(PAYLOAD_B)
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup))
        self.assertEqual(code, 1, out)
        self.assertEqual((self.dest / "Deck A.pdf").read_bytes(), b"corrupt")
        code, out = self.run_main("--dest", str(self.dest), "--from-dir", str(self.backup), "--force")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.dest / "Deck A.pdf").read_bytes(), PAYLOAD_A)


class CheckModeTests(TempDirCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_manifest()

    def test_check_never_writes_and_reports_missing(self) -> None:
        dest = self.temp / "never-created"
        code, out = self.run_main("--dest", str(dest), "--check")
        self.assertEqual(code, 1)
        self.assertFalse(dest.exists())
        self.assertIn("[missing]", out)
        self.assertIn("https://example.invalid/a", out)

    def test_check_reports_mismatch_and_ok(self) -> None:
        dest = self.temp / "dest"
        dest.mkdir()
        (dest / "Deck A.pdf").write_bytes(PAYLOAD_A)
        (dest / "Deck B.pdf").write_bytes(b"x" * len(PAYLOAD_B))
        opener = FakeOpener({})
        code, out = self.run_main("--dest", str(dest), "--check", opener=opener)
        self.assertEqual(code, 1)
        self.assertIn("[ok]      Deck A.pdf", out)
        self.assertIn("[hash-mismatch] Deck B.pdf", out)
        self.assertEqual(opener.requests, [])
        self.assertEqual((dest / "Deck B.pdf").read_bytes(), b"x" * len(PAYLOAD_B))

    def test_check_passes_when_everything_is_present(self) -> None:
        dest = self.temp / "dest"
        dest.mkdir()
        (dest / "Deck A.pdf").write_bytes(PAYLOAD_A)
        (dest / "Deck B.pdf").write_bytes(PAYLOAD_B)
        code, out = self.run_main("--dest", str(dest), "--check")
        self.assertEqual(code, 0, out)
        self.assertIn("All reference decks are verified", out)

    def test_default_destination_follows_pt_research_home_and_never_the_real_config(self) -> None:
        code, out = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn(str(self.home / "local-references"), out)
        explicit = self.temp / "explicit"
        with mock.patch.dict(os.environ, {"PT_LOCAL_REFERENCES_DIR": str(explicit)}):
            self.assertIn(str(explicit), self.run_main("--check")[1])

    def test_check_cannot_be_combined_with_from_dir(self) -> None:
        with mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(self.run_main("--check", "--from-dir", str(self.temp))[0], 2)


class DownloadTests(TempDirCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_manifest()
        self.dest = self.temp / "dest"

    def test_download_verifies_and_places_files_atomically(self) -> None:
        opener = FakeOpener({"example.invalid/a": PAYLOAD_A, "example.invalid/b": PAYLOAD_B})
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.dest / "Deck A.pdf").read_bytes(), PAYLOAD_A)
        self.assertEqual(self.leftovers(self.dest), [])
        # a second run is a no-op: nothing is requested for verified files
        opener2 = FakeOpener({})
        self.assertEqual(self.run_main("--dest", str(self.dest), opener=opener2)[0], 0)
        self.assertEqual(opener2.requests, [])

    def test_wrong_bytes_are_rejected_and_discarded(self) -> None:
        opener = FakeOpener({"example.invalid/a": PAYLOAD_A[:-1] + b"Z", "example.invalid/b": PAYLOAD_B + b"more"})
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 1, out)
        self.assertFalse((self.dest / "Deck A.pdf").exists())
        self.assertFalse((self.dest / "Deck B.pdf").exists())
        self.assertEqual(self.leftovers(self.dest), [])
        self.assertIn("[FAILED]", out)

    def test_short_download_is_rejected(self) -> None:
        opener = FakeOpener({"example.invalid/a": PAYLOAD_A[:10], "example.invalid/b": PAYLOAD_B})
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 1, out)
        self.assertFalse((self.dest / "Deck A.pdf").exists())
        self.assertTrue((self.dest / "Deck B.pdf").is_file())

    def test_alternate_url_is_tried_after_a_failure(self) -> None:
        opener = FakeOpener({"example.invalid/a": PAYLOAD_A, "example.invalid/b2": PAYLOAD_B})
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 0, out)
        self.assertTrue(any(u.endswith("/b") for u in opener.requests) and any(u.endswith("/b2") for u in opener.requests))

    def test_network_failure_reports_manual_steps(self) -> None:
        code, out = self.run_main("--dest", str(self.dest), opener=FakeOpener({}))
        self.assertEqual(code, 1)
        self.assertIn("network disabled in tests", out)
        self.assertIn("exact file names", out)
        self.assertEqual(self.leftovers(self.dest), [])

    def test_oversized_download_is_aborted(self) -> None:
        opener = FakeOpener({"example.invalid/a": PAYLOAD_A * 3, "example.invalid/b": PAYLOAD_B})
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 1, out)
        self.assertIn("larger than the expected", out)
        self.assertEqual(self.leftovers(self.dest), [])

    def test_drive_confirmation_page_is_followed(self) -> None:
        interstitial = (
            b'<html><form id="download-form" action="https://drive.usercontent.example/download" method="get">'
            b'<input type="hidden" name="id" value="FILEID"><input type="hidden" name="export" value="download">'
            b'<input type="hidden" name="confirm" value="t"><input type="hidden" name="uuid" value="u-1"></form></html>'
        )
        opener = FakeOpener({
            "example.invalid/a": lambda: FakeResponse(interstitial, "text/html; charset=utf-8", "https://drive.google.com/uc"),
            "drive.usercontent.example/download": PAYLOAD_A,
            "example.invalid/b": PAYLOAD_B,
        })
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 0, out)
        followed = [u for u in opener.requests if "drive.usercontent.example" in u][0]
        self.assertIn("confirm=t", followed)
        self.assertIn("id=FILEID", followed)
        self.assertIn("uuid=u-1", followed)

    def test_html_error_page_is_not_kept(self) -> None:
        opener = FakeOpener({
            "example.invalid/a": lambda: FakeResponse(b"<html>Quota exceeded</html>", "text/html"),
            "example.invalid/b": PAYLOAD_B,
        })
        code, out = self.run_main("--dest", str(self.dest), opener=opener)
        self.assertEqual(code, 1)
        self.assertIn("web page instead of the file", out)
        self.assertFalse((self.dest / "Deck A.pdf").exists())

    def test_drive_confirm_url_parsers(self) -> None:
        legacy = '<a href="/uc?export=download&amp;confirm=AbC1&amp;id=XYZ">Download anyway</a>'
        self.assertEqual(fetch.drive_confirm_url(legacy, "https://drive.google.com/uc?id=XYZ"),
                         "https://drive.google.com/uc?export=download&confirm=AbC1&id=XYZ")
        self.assertIsNone(fetch.drive_confirm_url("<html>nothing</html>", "https://drive.google.com/"))


def synthetic_pdf(jpeg: bytes) -> bytes:
    """A minimal PDF with two pages; page 2 holds one JPEG image and one Flate image."""

    parts = [
        b"%PDF-1.7\n",
        b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n",
        b"2 0 obj\n<</Type/Pages/Count 2/Kids[ 3 0 R 4 0 R ]>>\nendobj\n",
        b"3 0 obj\n<</Type/Page/Parent 2 0 R/Resources<<>>>>\nendobj\n",
        b"4 0 obj\n<</Type/Page/Parent 2 0 R/Resources<</XObject<</ImgA 5 0 R/ImgB 6 0 R>>>>>>\nendobj\n",
        b"5 0 obj\r\n<</Type/XObject/Subtype/Image/Width 4/Height 3/ColorSpace/DeviceRGB/BitsPerComponent 8/Filter/DCTDecode/Length "
        + str(len(jpeg)).encode() + b">>\r\nstream\r\n" + jpeg + b"\r\nendstream\r\nendobj\r\n",
        b"6 0 obj\n<</Type/XObject/Subtype/Image/Width 2/Height 2/ColorSpace/DeviceRGB/BitsPerComponent 8/Filter/FlateDecode/Length 4>>\nstream\nabcd\nendstream\nendobj\n",
        b"trailer\n<</Root 1 0 R>>\n%%EOF\n",
    ]
    return b"".join(parts)


class DerivedImageTests(TempDirCase):
    # Bytes need not be decodable: extraction only copies the DCT stream (it contains "endobj" on purpose).
    JPEG = b"\xff\xd8\xff\xe0 fake jpeg endobj 12 0 obj stream \xff\xd9"

    def spec(self, **overrides: object) -> dict:
        spec = {"output": "p2-image0.png", "source_deck": "Deck A.pdf", "page": 2, "xobject": "ImgA", "width": 4, "height": 3,
                "jpeg_sha256": sha(self.JPEG)}
        spec.update(overrides)
        return spec

    def test_extracts_the_named_jpeg_stream(self) -> None:
        pdf = synthetic_pdf(self.JPEG)
        self.assertEqual(fetch.extract_jpeg(pdf, 2, "ImgA", 4, 3), self.JPEG)
        with self.assertRaises(fetch.FetchError):
            fetch.extract_jpeg(pdf, 2, "ImgA", 5, 3)  # wrong dimensions
        with self.assertRaises(fetch.FetchError):
            fetch.extract_jpeg(pdf, 2, "ImgB", 2, 2)  # not a JPEG
        with self.assertRaises(fetch.FetchError):
            fetch.extract_jpeg(pdf, 1, "ImgA", 4, 3)  # not on that page
        with self.assertRaises(fetch.FetchError):
            fetch.extract_jpeg(pdf, 9, "ImgA", 4, 3)

    def test_regeneration_writes_jpg_without_pillow_and_never_overwrites(self) -> None:
        dest = self.temp / "dest"
        dest.mkdir()
        (dest / "Deck A.pdf").write_bytes(synthetic_pdf(self.JPEG))
        manifest = fake_manifest(derived=[self.spec()])
        lines: list[str] = []
        with mock.patch.dict(sys.modules, {"PIL": None}):
            self.assertEqual(fetch.regenerate_images(manifest, dest, False, lines.append), 0)
        target = dest / "source-images" / "p2-image0.jpg"
        self.assertEqual(target.read_bytes(), self.JPEG)
        self.assertEqual(self.leftovers(dest), [])
        target.write_bytes(b"user edit")
        with mock.patch.dict(sys.modules, {"PIL": None}):
            fetch.regenerate_images(manifest, dest, False, lines.append)
        self.assertEqual(target.read_bytes(), b"user edit")

    def test_hash_mismatch_of_extracted_stream_is_a_failure(self) -> None:
        dest = self.temp / "dest"
        dest.mkdir()
        (dest / "Deck A.pdf").write_bytes(synthetic_pdf(self.JPEG))
        lines: list[str] = []
        with mock.patch.dict(sys.modules, {"PIL": None}):
            problems = fetch.regenerate_images(fake_manifest(derived=[self.spec(jpeg_sha256="0" * 64)]), dest, False, lines.append)
        self.assertEqual(problems, 1)
        self.assertFalse((dest / "source-images").exists() and any((dest / "source-images").iterdir()))

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is unavailable")
    def test_regeneration_converts_to_png_with_pillow(self) -> None:
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (4, 3), (200, 30, 30)).save(buffer, "JPEG")
        jpeg = buffer.getvalue()
        dest = self.temp / "dest"
        dest.mkdir()
        (dest / "Deck A.pdf").write_bytes(synthetic_pdf(jpeg))
        fetch.regenerate_images(fake_manifest(derived=[self.spec(jpeg_sha256=sha(jpeg))]), dest, False, lambda _m: None)
        image = Image.open(dest / "source-images" / "p2-image0.png")
        self.assertEqual((image.format, image.size), ("PNG", (4, 3)))

    def test_main_extracts_images_after_a_verified_restore(self) -> None:
        pdf = synthetic_pdf(self.JPEG)
        manifest = fake_manifest(payload_a=pdf, derived=[self.spec()])
        self.write_manifest(manifest)
        backup = self.temp / "backup"
        backup.mkdir()
        (backup / "Deck A.pdf").write_bytes(pdf)
        (backup / "Deck B.pdf").write_bytes(PAYLOAD_B)
        dest = self.temp / "dest"
        with mock.patch.dict(sys.modules, {"PIL": None}):
            code, out = self.run_main("--dest", str(dest), "--from-dir", str(backup))
        self.assertEqual(code, 0, out)
        self.assertTrue((dest / "source-images" / "p2-image0.jpg").is_file())
        code, out = self.run_main("--dest", str(dest), "--check")
        self.assertEqual(code, 0, out)
        self.assertIn("p2-image0.png: present", out)


class DocumentationWiringTests(unittest.TestCase):
    def test_readme_agents_and_skill_point_to_the_restore_steps(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Restoring private CYPT reference decks (not redistributed)", readme)
        for needle in ("PT_RESEARCH_HOME", "fetch_local_references.py", "--check", "local-references.manifest.json", "Team Singapore", "Team Slovakia"):
            self.assertIn(needle, readme)
        for relative in ("AGENTS.md", "skills/cypt-slide-template/SKILL.md", "skills/cypt-slide-template/README.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("fetch_local_references.py", text, relative)
            self.assertIn("PT_RESEARCH_HOME", text, relative)
        skill = (ROOT / "skills/cypt-slide-template/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ask the user before", skill)

    def test_example_config_documents_the_private_data_directory(self) -> None:
        example = json.loads((ROOT / "local.paths.example.json").read_text(encoding="utf-8"))
        self.assertIn("PT_RESEARCH_HOME", example["_comment"])
        self.assertIn("PT_LOCAL_REFERENCES_DIR", example)


if __name__ == "__main__":
    unittest.main()
