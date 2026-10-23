import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "mirror_releases.py"
if not SOURCE.exists():
    SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "mirror_games.py"
SPEC = importlib.util.spec_from_file_location("mirror", SOURCE)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class CatalogTests(unittest.TestCase):
    def record(self, **changes):
        value = {"file": "Game.zip", "serial": "SLUS-00001", "title": "Game", "url": "/downloads/ps1/v1/Game.zip", "bytes": 42, "sha256": "a" * 64}
        value.update(changes)
        return value

    def test_ps1_only(self):
        self.assertEqual(len(M.catalog_records([self.record(), self.record(url="/downloads/n64/Game.zip"), self.record(ready=False)])), 1)

    def test_unsafe_name(self):
        for name in ["../Game.zip", "/Game.zip", "Game.exe"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                M.catalog_records([self.record(file=name)])

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            M.catalog_records([self.record(), self.record()])

    def test_bad_hash(self):
        for digest in ["f" * 63, "G" * 64, ""]:
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                M.catalog_records([self.record(sha256=digest)])

    def test_bad_size(self):
        for size in [-1, 0, 2_000_000_000, "42"]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                M.catalog_records([self.record(bytes=size)])

    def test_url_escape(self):
        for url in ["/downloads/ps1/%2e%2e/Game.zip", "/downloads/ps1/Game.zip?download=1", "/downloads/ps1/Game.zip#fragment"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                M.catalog_records([self.record(url=url)])


class ZipTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "Game.zip"
        self.native = b"synthetic-native-fixture-never-executed"
        self.identity = hashlib.sha256(json.dumps({"serial": "SLUS-00001", "sha1": ["1" * 40], "disc_fp": "fixture"}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.metadata = {"schema": 1, "product": "ps1-game-player", "serial": "SLUS-00001", "identity": self.identity, "feed": M.ORIGIN + "/programs/ps1/games/" + self.identity + "/latest.json", "native_baseline": {"build-release/Game.exe": hashlib.sha256(self.native).hexdigest()}}

    def tearDown(self):
        self.directory.cleanup()

    def fixture(self, extra=None, omit=None, metadata=None):
        members = {"Game/game.toml": '[game]\nid="SLUS-00001"\n[prepare_disc]\nknown_sha1=["' + "1" * 40 + '"]\n[netplay]\nrequired_disc_fp="fixture"\n', "Game/build-release/Game.exe": self.native, "Game/game-update.json": json.dumps(metadata or self.metadata)}
        members.update({"Game/" + n: "synthetic-updater-fixture" for n in ["game_updates.py", "game-launch.py", "Start-Update.cmd", "Start-Game.cmd", "GAME-UPDATES.txt"]})
        members.update(extra or {})
        if omit:
            members.pop(omit)
        with zipfile.ZipFile(self.path, "w") as archive:
            for name, value in members.items():
                archive.writestr(name, value)

    def test_good(self):
        self.fixture()
        M.validate_zip(self.path, {"serial": "SLUS-00001"})

    def test_serial_mismatch(self):
        self.fixture()
        with self.assertRaises(ValueError):
            M.validate_zip(self.path, {"serial": "SLUS-00002"})

    def test_missing_updater(self):
        self.fixture(omit="Game/Start-Update.cmd")
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_wrong_revision(self):
        self.fixture(metadata={**self.metadata, "identity": "0" * 64})
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_wrong_feed(self):
        self.fixture(metadata={**self.metadata, "feed": "https://example.com/fix.json"})
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_native_tamper(self):
        self.fixture(extra={"Game/build-release/Game.exe": b"changed"})
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_original_media_and_saves(self):
        for name in ["disc.iso", "disc.chd", "disc.cue", "SCPH1001.BIN", "card.mcd", "save.sav"]:
            with self.subTest(name=name):
                self.fixture(extra={"Game/" + name: b"not-a-real-media-file"})
                with self.assertRaises(ValueError):
                    M.validate_zip(self.path)

    def test_path_escape(self):
        for name in ["../escape", "/absolute", "Game/C:/absolute", "Game/dir\\escape"]:
            with self.subTest(name=name):
                self.fixture(extra={name: "synthetic"})
                with self.assertRaises(ValueError):
                    M.validate_zip(self.path)

    def test_multiple_roots(self):
        self.fixture(extra={"Other/a.txt": "synthetic"})
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_case_collision(self):
        self.fixture(extra={"Game/START-UPDATE.CMD": "synthetic"})
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)

    def test_symlink(self):
        self.fixture()
        with zipfile.ZipFile(self.path, "a") as archive:
            info = zipfile.ZipInfo("Game/link")
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "outside")
        with self.assertRaises(ValueError):
            M.validate_zip(self.path)


class ProgramTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "Program.zip"
        self.record = {"product": "ps1-remaker-public", "version": "0.20.0-public-beta", "file": "Program.zip", "bytes": 42, "sha256": "a" * 64, "url": "/downloads/programs/ps1/Program.zip"}

    def tearDown(self):
        self.directory.cleanup()

    def fixture(self, extra=None, manifest=None):
        files = {"ps1_remaker.py": b"synthetic-script-never-executed"}
        inventory = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        metadata = manifest or {"schema": 1, "product": "ps1-remaker-public", "version": "0.20.0-public-beta", "files": inventory}
        files.update(extra or {})
        with zipfile.ZipFile(self.path, "w") as archive:
            for name, data in files.items():
                archive.writestr("PS1-Remaker-Public/" + name, data)
            archive.writestr("PS1-Remaker-Public/UPDATE-MANIFEST.json", json.dumps(metadata))

    def test_valid_program(self):
        self.fixture()
        M.validate_program_zip(self.path, self.record)
        self.assertEqual(M.program_records({"programs": [self.record]}), [self.record])

    def test_wrong_product(self):
        self.fixture()
        with self.assertRaises(ValueError):
            M.validate_program_zip(self.path, {**self.record, "product": "ps1-player-public"})

    def test_wrong_version(self):
        self.fixture()
        with self.assertRaises(ValueError):
            M.validate_program_zip(self.path, {**self.record, "version": "0.21.0"})

    def test_undeclared_program_file(self):
        self.fixture(extra={"extra.py": b"synthetic"})
        with self.assertRaises(ValueError):
            M.validate_program_zip(self.path, self.record)

    def test_tampered_program_file(self):
        self.fixture(extra={"ps1_remaker.py": b"changed"})
        with self.assertRaises(ValueError):
            M.validate_program_zip(self.path, self.record)

    def test_unapproved_program_url(self):
        with self.assertRaises(ValueError):
            M.program_records({"programs": [{**self.record, "url": "/downloads/programs/xbox/Program.zip"}]})


if __name__ == "__main__":
    unittest.main()
