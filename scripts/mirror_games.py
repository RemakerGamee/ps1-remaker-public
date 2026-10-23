"""Mirror verified RetroRemakes PS1 game ZIPs to GitHub Releases.

Uses the authenticated GitHub CLI. Never executes, extracts or modifies a game.
The catalog must come from the final reviewed website release snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import tomllib
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ORIGIN = "https://retroremakes.retroremakes.chatgpt.site"


def validate_zip(path, record=None, require_updater=True):
    """Read-only CRC/path/obvious-disc-and-save exclusion checks."""
    with zipfile.ZipFile(path) as archive:
        names = set()
        expanded = 0
        for info in archive.infolist():
            name = info.filename.rstrip("/")
            relative = PurePosixPath(name)
            if not name or relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or str(relative) != name:
                raise ValueError("Unsafe ZIP member")
            if name.casefold() in {n.casefold() for n in names} or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Duplicate ZIP member or symbolic link")
            names.add(name)
            expanded += info.file_size
            if expanded > 4_000_000_000 or len(names) > 20_000:
                raise ValueError("ZIP expansion bound exceeded")
            if relative.suffix.lower() in {".iso", ".chd", ".cue", ".img", ".mdf", ".ecm", ".mcd", ".mcr", ".vmp", ".sav", ".srm"} or re.fullmatch(r"scph[-_0-9a-z]*\.bin", relative.name, re.I):
                raise ValueError("Game ZIP contains a disc, BIOS or player-save filename")
        bad = archive.testzip()
        if bad:
            raise ValueError("ZIP CRC mismatch: " + bad)
        if not any(name.endswith("/game.toml") for name in names):
            raise ValueError("No native project metadata")
        roots = {name.split("/")[0] for name in names}
        if len(roots) != 1:
            raise ValueError("Expected one game archive root")
        prefix = next(iter(roots)) + "/"
        config = tomllib.loads(archive.read(prefix + "game.toml").decode("utf-8-sig"))
        if record and config["game"]["id"] != record["serial"]:
            raise ValueError("Catalog serial does not match game project")
        if require_updater:
            required = {"game-update.json", "game_updates.py", "game-launch.py", "Start-Update.cmd", "Start-Game.cmd", "GAME-UPDATES.txt"}
            if not all(prefix + name in names for name in required):
                raise ValueError("Game does not include the online updater")
            metadata = json.loads(archive.read(prefix + "game-update.json"))
            identity_data = {"serial": config["game"]["id"], "sha1": sorted(config.get("prepare_disc", {}).get("known_sha1", [])), "disc_fp": config.get("netplay", {}).get("required_disc_fp", "")}
            identity = hashlib.sha256(json.dumps(identity_data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if not identity_data["sha1"] or any(not re.fullmatch(r"[a-fA-F0-9]{40}", value) for value in identity_data["sha1"]) or metadata.get("schema") != 1 or metadata.get("product") != "ps1-game-player" or metadata.get("identity") != identity or metadata.get("serial") != config["game"]["id"] or metadata.get("feed") != ORIGIN + "/programs/ps1/games/" + identity + "/latest.json":
                raise ValueError("Game updater revision metadata mismatch")
            if not metadata.get("native_baseline"):
                raise ValueError("Game updater native baseline missing")
            for name, digest in metadata["native_baseline"].items():
                if not name.startswith("build-release/") or not name.lower().endswith(".exe") or hashlib.sha256(archive.read(prefix + name)).hexdigest() != digest:
                    raise ValueError("Game updater native baseline mismatch")


def catalog_records(catalog):
    records = catalog.get("releases", []) if isinstance(catalog, dict) else catalog
    result = []
    seen = set()
    for record in records:
        url = record.get("url", "")
        if record.get("ready", True) is False or not url.startswith("/downloads/ps1/"):
            continue
        name = record["file"]
        if name != Path(name).name or not name.endswith(".zip") or name in seen or any(c in name for c in ("\\", ":", "\n", "\r", "\0")):
            raise ValueError("Unsafe or duplicate release filename")
        if not re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", "")):
            raise ValueError("Missing SHA256")
        if not isinstance(record.get("bytes"), int) or not 0 < record["bytes"] < 2_000_000_000:
            raise ValueError("Invalid release length")
        if ".." in urllib.parse.unquote(url).split("/") or "?" in url or "#" in url:
            raise ValueError("Unsafe release URL")
        seen.add(name)
        result.append(record)
    if not result:
        raise ValueError("No eligible PS1 releases")
    return result


def program_records(catalog):
    records = catalog.get("programs", []) if isinstance(catalog, dict) else []
    result = []
    seen = set()
    prefixes = {"ps1-remaker-public": "/downloads/programs/ps1/", "ps1-player-public": "/downloads/programs/ps1/player/"}
    for record in records:
        product = record.get("product")
        if product not in prefixes or product in seen or not record.get("url", "").startswith(prefixes[product]):
            raise ValueError("Unexpected program product or URL")
        # Reuse size/hash/filename validation without relaxing the game selector.
        candidate = dict(record, url="/downloads/ps1/" + record["file"])
        catalog_records([candidate])
        if record["url"] != prefixes[product] + record["file"] or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", record.get("version", "")):
            raise ValueError("Unexpected program filename or version")
        seen.add(product)
        result.append(record)
    return result


def validate_program_zip(path, record):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        files = [name for name in names if not name.endswith("/")]
        if len(names) != len(set(n.casefold() for n in names)):
            raise ValueError("Duplicate program ZIP member")
        prefix = "PS1-Remaker-Public/" if record["product"] == "ps1-remaker-public" else "PS1-Player-Public/"
        for info in archive.infolist():
            name = info.filename.rstrip("/")
            relative = PurePosixPath(name)
            if not info.filename.startswith(prefix) or relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or str(relative) != name or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe program ZIP member")
            if relative.suffix.lower() in {".iso", ".chd", ".cue", ".img", ".mdf", ".ecm", ".mcd", ".mcr", ".vmp", ".sav", ".srm"} or re.fullmatch(r"scph[-_0-9a-z]*\.bin", relative.name, re.I):
                raise ValueError("Program ZIP contains disc/BIOS/save filename")
        if archive.testzip():
            raise ValueError("Program ZIP CRC mismatch")
        manifest_name = prefix + "UPDATE-MANIFEST.json"
        manifest = json.loads(archive.read(manifest_name))
        if manifest.get("schema") != 1 or manifest.get("product") != record["product"] or manifest.get("version") != record["version"]:
            raise ValueError("Program product/version mismatch")
        declared = manifest.get("files", {})
        if set(files) != {prefix + name for name in declared} | {manifest_name}:
            raise ValueError("Program manifest inventory mismatch")
        for name, digest in declared.items():
            if hashlib.sha256(archive.read(prefix + name)).hexdigest() != digest:
                raise ValueError("Program manifest file hash mismatch")


def download(record, destination):
    digest = hashlib.sha256()
    total = 0
    request = urllib.request.Request(ORIGIN + record["url"], headers={"User-Agent": "RetroRemakes-PS1-Release-Mirror/1"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        allowed = "/downloads/programs/ps1/" if record.get("product") else "/downloads/ps1/"
        if not response.url.startswith(ORIGIN + allowed):
            raise ValueError("Download redirected outside approved PS1 origin")
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > record["bytes"]:
                raise ValueError("Download exceeded declared length")
            digest.update(block)
            output.write(block)
    if total != record["bytes"] or digest.hexdigest() != record["sha256"]:
        destination.unlink(missing_ok=True)
        raise ValueError("Download identity mismatch: " + record["file"])


def gh(*arguments, capture=False):
    return subprocess.run(["gh", *arguments], check=True, text=True, capture_output=capture)


def mirror(record, repository, working, dry_run):
    program = bool(record.get("product"))
    tag = (record["product"] + "-v" + record["version"]) if program else "game-" + record["sha256"][:24]
    latest = "true" if record.get("product") == "ps1-remaker-public" else "false"
    local = working / record["file"]
    existing = None
    if not dry_run:
        view = subprocess.run(["gh", "api", "repos/" + repository + "/releases/tags/" + tag], capture_output=True, text=True)
        if not view.returncode:
            existing = json.loads(view.stdout)
            assets = [a for a in existing.get("assets", []) if a["name"] == record["file"]]
            if assets:
                asset = assets[0]
                if asset.get("size") != record["bytes"] or asset.get("digest") != "sha256:" + record["sha256"]:
                    raise ValueError("Existing GitHub asset identity differs; refusing replacement")
                if existing.get("draft"):
                    gh("release", "edit", tag, "--repo", repository, "--draft=false", "--latest=" + latest)
                return {"file": record["file"], "sha256": record["sha256"], "bytes": record["bytes"], "uploaded": True, "reused": True, "release": existing["html_url"], "download_url": asset["browser_download_url"]}
        elif "404" not in view.stderr:
            raise RuntimeError("GitHub release lookup failed; no upload attempted")
    download(record, local)
    if program:
        validate_program_zip(local, record)
    else:
        validate_zip(local, record)
    if dry_run:
        local.unlink()
        return {"file": record["file"], "sha256": record["sha256"], "bytes": record["bytes"], "download_verified": True, "uploaded": False}
    if existing is None:
        notes = working / "release-notes.md"
        notes.write_text(
            ("RetroRemakes public PS1 Studio/Player update.\n\n" if program else "Experimental native PS1 project: " + (record.get("title") or record["serial"]) + " (" + record["serial"] + ").\n\n") +
            "Supply your own original disc and supported BIOS. No disc or BIOS is included. Compatibility and gameplay are not guaranteed. Existing license terms remain in the ZIP.\n\n"
            "Website: " + ORIGIN + record["url"] + "\n\nSHA256: `" + record["sha256"] + "`\nBytes: " + str(record["bytes"]) + "\n",
            encoding="utf-8",
        )
        title = (record.get("title") or record.get("serial") or record["file"]) + (" — " + record["serial"] if not program else " " + record["version"])
        gh("release", "create", tag, "--repo", repository, "--draft", "--title", title, "--notes-file", str(notes))
    gh("release", "upload", tag, str(local), "--repo", repository)
    verified = json.loads(gh("api", "repos/" + repository + "/releases/tags/" + tag, capture=True).stdout)
    asset = next(a for a in verified["assets"] if a["name"] == record["file"])
    if asset["size"] != record["bytes"] or asset.get("digest") != "sha256:" + record["sha256"]:
        raise ValueError("GitHub uploaded asset failed identity verification")
    gh("release", "edit", tag, "--repo", repository, "--draft=false", "--latest=" + latest)
    local.unlink()
    return {"file": record["file"], "sha256": record["sha256"], "bytes": record["bytes"], "uploaded": True, "release": verified["html_url"], "download_url": asset["browser_download_url"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--repo", default="RemakerGamee/ps1-remaker-public")
    parser.add_argument("--report", type=Path, default=Path("github-mirror-report.json"))
    parser.add_argument("--verify-downloads-only", action="store_true")
    arguments = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", arguments.repo):
        raise ValueError("Invalid GitHub repository")
    catalog = json.loads(arguments.catalog.read_text(encoding="utf-8"))
    games = catalog_records(catalog)
    programs = program_records(catalog)
    records = programs + games
    results = []
    if not arguments.verify_downloads_only:
        gh("auth", "status")
    with tempfile.TemporaryDirectory(prefix="ps1-game-mirror-") as temporary:
        for index, record in enumerate(records):
            result = mirror(record, arguments.repo, Path(temporary), arguments.verify_downloads_only)
            results.append(result)
            arguments.report.write_text(json.dumps({"repository": arguments.repo, "expected_games": len(games), "expected_programs": len(programs), "verified_assets": len(results), "complete": len(results) == len(records), "results": results}, indent=2) + "\n", encoding="utf-8")
            print(f"{index + 1}/{len(records)} {record['file']}", flush=True)


if __name__ == "__main__":
    main()
