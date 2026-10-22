# RetroRemakes PS4 Studio update channel

This dedicated `ps4-studio-updates` branch distributes PS4 Studio. The PS1 main branch is separate.

Stable manifest: `updates/ps4/stable.json`.

Packages contain the complete Python application source, the Cartridge integration and its licenses, tests, research catalog and installation instructions. No games, firmware, keys, user settings or generated game projects are included.

PS4 Studio v0.1.2 adds startup/manual update checks, verified downloads, restart-to-install, backups and rollback for handled replacement failures. Python 3.11+ with Tk is required. Windows installation behavior still needs validation on a Windows PC; 42 core/Cartridge/update tests pass on Linux.

For maintenance, extract a package and use `build_update_release.py`. Publish immutable packages first; then update the stable manifest with the correct app ID, semantic version, byte size, SHA-256 and immutable HTTPS package URL.
