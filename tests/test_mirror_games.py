import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
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
                info = zipfile.ZipInfo(name)
                info.filename = name  # Keep the deliberately unsafe raw spelling on Windows.
                archive.writestr(info, value)

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


class PublicationTests(unittest.TestCase):
    def record(self):
        return {"file": "Game.zip", "serial": "SLUS-00001", "title": "Synthetic", "bytes": 42, "sha256": "a" * 64, "url": "/downloads/ps1/Game.zip"}

    def test_draft_recovery_uses_release_id(self):
        record = self.record()
        tag = "game-" + "a" * 24
        asset = {"name": "Game.zip", "size": 42, "digest": "sha256:" + "a" * 64, "browser_download_url": "https://github.com/example/asset"}
        draft = {"id": 17, "draft": True, "html_url": "https://github.com/example/draft", "assets": [asset]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(M, "download") as download, patch.object(M, "mutate_json", return_value={**draft, "draft": False}) as mutate:
            result = M.mirror(record, "RemakerGamee/ps1-remaker-public", Path(temporary), False, {tag: draft})
        download.assert_not_called()
        self.assertEqual(mutate.call_args.args[0], "repos/RemakerGamee/ps1-remaker-public/releases/17")
        self.assertEqual(mutate.call_args.args[1], "PATCH")
        self.assertTrue(result["reused"])

    def test_new_upload_uses_asset_response_and_release_id(self):
        record = self.record()
        created = {"id": 27, "draft": True}
        asset = {"size": 42, "digest": "sha256:" + "a" * 64, "browser_download_url": "https://github.com/example/asset"}
        published = {"id": 27, "html_url": "https://github.com/example/release"}
        with tempfile.TemporaryDirectory() as temporary, patch.object(M, "download", side_effect=lambda r, p: p.write_bytes(b"synthetic")), patch.object(M, "validate_zip"), patch.object(M, "mutate_json", side_effect=[created, asset, published]) as mutate:
            result = M.mirror(record, "RemakerGamee/ps1-remaker-public", Path(temporary), False, {})
        self.assertEqual(mutate.call_count, 3)
        self.assertIn("uploads.github.com/repos/RemakerGamee/ps1-remaker-public/releases/27/assets?name=Game.zip", mutate.call_args_list[1].args[0])
        self.assertEqual(mutate.call_args_list[2].args[0], "repos/RemakerGamee/ps1-remaker-public/releases/27")
        self.assertTrue(result["uploaded"])

    def test_draft_unexpected_asset_refused(self):
        record = self.record()
        tag = "game-" + "a" * 24
        draft = {"id": 17, "draft": True, "assets": [{"name": "Unexpected.zip"}]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(M, "download") as download, patch.object(M, "mutate_json") as mutate:
            with self.assertRaises(ValueError):
                M.mirror(record, "RemakerGamee/ps1-remaker-public", Path(temporary), False, {tag: draft})
        download.assert_not_called()
        mutate.assert_not_called()


class RateLimitTests(unittest.TestCase):
    def error(self, headers="", body="secondary rate limit"):
        return subprocess.CalledProcessError(1, ["gh", "api"], output="HTTP/2.0 403 Forbidden\r\n" + headers + "\r\n" + body, stderr="HTTP403")

    def test_header_parse(self):
        headers, body = M.response_parts('HTTP/2.0 201 Created\r\nContent-Type: application/json\r\n\r\n{"id":1}')
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(json.loads(body), {"id": 1})

    def test_retry_after_honored(self):
        error = self.error("Retry-After: 2\r\n")
        self.assertEqual(M.rate_delay(error, 0), 2)
        response = subprocess.CompletedProcess(["gh"], 0, stdout='HTTP/2.0 200 OK\r\n\r\n{"id":1}')
        with patch.object(M, "LAST_MUTATION", 0.0), patch.object(M, "gh", side_effect=[error, response]) as gh, patch.object(M.time, "sleep") as sleep, patch.object(M.time, "monotonic", return_value=100):
            result = M.mutate_json("repos/owner/repo/releases", "POST")
        self.assertEqual(result, {"id": 1})
        self.assertEqual(gh.call_count, 2)
        sleep.assert_called_once_with(2)

    def test_primary_reset_honored(self):
        with patch.object(M.time, "time", return_value=100):
            self.assertEqual(M.rate_delay(self.error("X-RateLimit-Remaining: 0\r\nX-RateLimit-Reset: 160\r\n", "API rate limit exceeded"), 0), 61)

    def test_ambiguous_post_failure_not_retried(self):
        error = self.error("", "upstream connection failed")
        with patch.object(M, "LAST_MUTATION", 0.0), patch.object(M, "gh", side_effect=error) as gh, patch.object(M.time, "sleep"), patch.object(M.time, "monotonic", return_value=100):
            with self.assertRaises(subprocess.CalledProcessError):
                M.mutate_json("repos/owner/repo/releases", "POST")
        gh.assert_called_once()

    def test_wait_is_bounded(self):
        self.assertIsNone(M.rate_delay(self.error("Retry-After: 3601\r\n"), 0))

    def test_failed_report_keeps_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "catalog.json"
            report = root / "report.json"
            catalog.write_text(json.dumps([PublicationTests().record()]))
            with patch.object(sys, "argv", ["mirror", str(catalog), "--report", str(report)]), patch.object(M, "release_index", return_value={}), patch.object(M, "mirror", side_effect=RuntimeError("synthetic refusal")):
                with self.assertRaises(RuntimeError):
                    M.main()
            data = json.loads(report.read_text())
            self.assertEqual(data["status"], "failed")
            self.assertEqual(data["verified_assets"], 0)
            self.assertEqual(data["error"]["file"], "Game.zip")



class RemakerOnlyProgramTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"Builder.zip"
        self.record={"product":"ps1-remaker-builder-public","version":"0.21.2-public-beta","file":"Builder.zip","bytes":42,"sha256":"a"*64,"url":"/downloads/programs/ps1/remaker/Builder.zip"}
    def archive(self,player=False,missing=False):
        files={name:b"host fixture" for name in ("ps1_remaker.py","studio_ui.py","engines.py","app_update.py","Start-PS1-Remaker.cmd","history_store.py","player_template/player.py","player_template/player_core.py")}
        if player:files["Start-PS1-Player.cmd"]=b"excluded launcher"
        if missing:files.pop("player_template/player.py")
        manifest={"schema":1,"product":self.record["product"],"version":self.record["version"],"files":{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
        with zipfile.ZipFile(self.path,"w") as archive:
            for name,data in files.items():archive.writestr("PS1-Remaker-Only-Public/"+name,data)
            archive.writestr("PS1-Remaker-Only-Public/UPDATE-MANIFEST.json",json.dumps(manifest))
    def test_builder_has_distinct_product_path_and_valid_templates(self):
        self.archive();M.validate_program_zip(self.path,self.record)
        self.assertEqual(M.program_records({"programs":[self.record]}),[self.record])
    def test_builder_refuses_standalone_player_launcher(self):
        self.archive(player=True)
        with self.assertRaises(ValueError):M.validate_program_zip(self.path,self.record)
    def test_builder_requires_output_player_template(self):
        self.archive(missing=True)
        with self.assertRaises(ValueError):M.validate_program_zip(self.path,self.record)
    def test_builder_does_not_accept_combined_feed_path(self):
        with self.assertRaises(ValueError):M.program_records({"programs":[{**self.record,"url":"/downloads/programs/ps1/Builder.zip"}]})

    def test_combined_product_rejects_nested_component_prefix(self):
        for path in ("/downloads/programs/ps1/player/Builder.zip","/downloads/programs/ps1/remaker/Builder.zip"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                M.program_records({"programs":[{**self.record,"product":"ps1-remaker-public","url":path}]})

if __name__ == "__main__":
    unittest.main()
