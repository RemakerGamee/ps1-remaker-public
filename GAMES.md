# PS1 game players

The catalog lists reviewed website packages. GitHub release downloads appear as verified mirroring completes; the first mirror is currently in progress. See the [game index](games/README.md). Game ZIPs are hosted in this repository's [Releases](https://github.com/RemakerGamee/ps1-remaker-public/releases) section. Each game and disc revision has a separate checksum-addressed release. The website remains the original download and online-update source.

These are experimental native player projects. Supply your own original game disc and supported BIOS. Neither is supplied here. Inclusion in the catalog does not establish successful gameplay or universal compatibility.

New downloads contain `Start-Update.cmd` for updates matched to that exact game and disc revision. Close that game's player before installing. Other game installations can remain open. Existing saves, settings, disc/BIOS paths and mods remain separate from update targets. The initial updater retrofit preserves each native game executable byte for byte.

The mirror workflow reads `games/catalog.json`, downloads each ZIP from the official HTTPS website, checks the exact size and SHA256, reads ZIP paths and CRCs without executing anything, verifies the per-game updater identity and native baseline, then uploads a draft GitHub Release. It publishes only after GitHub reports the expected asset size and SHA256. Existing matching releases are retained. A failed check stops that run and retains its report.

Preserve the individual packages' licenses and third-party notices. Checksum verification does not establish publisher signing. This repository does not change upstream license terms or guarantee game compatibility.
