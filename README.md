# RetroRemakes PS1 Remaker

Public beta **v0.21.10-public-beta** — Windows applications for experimental native PS1 projects.

Choose the download you need:

| Download | Includes | Start here |
| --- | --- | --- |
| [Remaker & Player](https://github.com/RemakerGamee/ps1-remaker-public/releases/download/ps1-remaker-public-v0.21.10-public-beta/PS1-Remaker-Public-v0.21.10-public-beta.zip) | Both applications | `Start-PS1-Remaker.cmd` or `Start-PS1-Player.cmd` |
| [Remaker only](https://github.com/RemakerGamee/ps1-remaker-public/releases/download/ps1-remaker-public-v0.21.10-public-beta/PS1-Remaker-Only-Public-v0.21.10-public-beta.zip) | Remaker, with the player resources required by generated projects | `Start-PS1-Remaker.cmd` |
| [Player only](https://github.com/RemakerGamee/ps1-remaker-public/releases/download/ps1-remaker-public-v0.21.10-public-beta/PS1-Player-Public-v0.21.10-public-beta.zip) | Player for an existing compatible game output | `Start-Player.cmd` |

Extract the entire archive. Python 3.11+ with Tcl/Tk is required. Building projects also requires a compatible C++ toolchain, CMake and Windows SDK. Each application edition uses its own update identity and approved feed.

Supply your own supported PS1 BIOS and matching game disc files. No BIOS or games are included. Building a game does not guarantee compatibility. Windows commercial-game gameplay and physical-controller coverage remain experimental.

The public ZIPs include source and preserved license notices. The bundled PSXRecomp engine uses the PolyForm Noncommercial license; see its complete terms inside the ZIP. This is a free noncommercial public beta.

## PS1 game players

The [game catalog](games/README.md) lists the 164 reviewed game projects from the website. All 164 game ZIPs have been mirrored to GitHub Releases. Each published asset size and GitHub SHA256 digest matches the reviewed website catalog; see the [verification report](games/verification.json). Every refreshed game ZIP includes `Start-Update.cmd` for fixes matched to its exact disc revision. Game project releases are separate from the public Studio/Player ZIP; users still supply their original disc and supported BIOS. Game inclusion does not guarantee gameplay compatibility.

Online updates download and verify a release before installation. Installation-specific locks allow unrelated games and Studio installations to keep running. Saves, settings, disc/BIOS paths and mods are protected from update targets. Shared Player fixes and game-specific fixes use separate feeds; neither automatically proves compatibility.

## Save states

The Player now has a visible **Save States (F7)** button. Choose one of 12 slots, press **S** to save or **L/Enter** to load, and **Escape** to return. States stay in the selected game Save folder, separately from memory-card saves. Use the same compatible game build and BIOS when restoring. Alundra 2 save/load and restart persistence were verified; other titles still need gameplay review.

## Disc matching correction

Disc matching correction for the published US Tomorrow Never Dies (SLUS-00975) and Akuji (SLUS-00715) builds. Matching game code is accepted across equivalent CUE/BIN layouts, including shared BIN/audio, INDEX 01 pregaps, trailing padding and 2048/2352-byte sector layouts. The fallback checks the exact native build, game serial and SHA-256 of the known game executables; Tomorrow Never Dies mission EXEs are checked too. Changed game code and wrong games/regions still require a matching build. Original exact disc hashes remain supported. Choose the CUE, not an individual BIN. BIOS selection does not change disc identity. The reported tester's exact dump was unavailable; this is not a claim that every US revision is supported. Saves, settings and existing Save States controls are preserved.


## Community uploads, diagnostics and progress

Adds previewable diagnostic reports to PS1 Player and Remaker, including optional sanitized log excerpts, offline report ZIP export, user-approved issue submission and optional support email. Adds build-stage progress reporting with exact counters when the tool provides them; other stages show activity without inventing a completion percentage. Adds community package submission for signed-in contributors, private validation/review and edition-specific website publication; submissions do not overwrite another contributor's version. Keeps public BIOS/disc requirements, private-player behavior, save states and existing disc matching. No BIOS, original discs, saves, user settings or native game builds are distributed in this application update. Commercial-game compatibility remains experimental.


## Export errors and batch history

Adds an All games error history with Copy all errors and Save all error reports in Remaker and Player. Batch failures are saved across games and restarts; an individual-game filter remains available. Exported reports include sanitized error messages and details, with optional bounded log excerpts. Reports exclude original discs, BIOS, saves and settings. Error-history storage and excerpts remain bounded; this does not collect unlimited game logs or memory dumps. Preserves save states, disc matching, private Player Updates, community submission review and build progress. The private update preserves the configured update feed; older installations without a configured feed can retain the manual ZIP update workflow.


## European PAL support and separate downloads

Clarifies and preserves European PAL PS1 disc support in Remaker. SLES and SCES disc identities use Europe metadata, and the game picker supports matching CUE/BIN and CHD discs without a USA-only title gate. Existing game-specific downloads still require the matching supported disc edition. Preserves Export Errors, saved all-game error history, save states, build progress, community submissions and private Player Updates. Existing update feeds and user data remain untouched. Synthetic PAL identity/selection checks do not establish full-game compatibility or a new remaster. Public downloads now provide separate Remaker-only, Player-only and combined packages, each following its own approved update feed.


## True Color (optional)

Adds a per-game Color mode choice in Renderer settings: Original (default) or True Color. On a compatible native build, True Color selects OpenGL and disables PS1 dithering/5-bit shaded-gradient quantization on eligible GPU output. The original textures, movies, guest VRAM readbacks and software rendering retain their original precision; this does not create missing source colors or HD artwork. The choice applies on the next launch through Remaker or Player. Unsupported builds and forced CPU presentation are refused with a clear message. Actual production-renderer gradient checks measured 249 red levels with True Color versus 32 with native dithering; this is a renderer test, not a retail gameplay claim. Keeps PAL disc support, all-game error export, save states, separate public program editions and private Player Updates. Community submission consent now explicitly identifies uploads as independent contributor versions rather than official RetroRemakes releases. Existing update feeds and user data are preserved.


## Verified disc container matching

Improves matching of supported PS1 discs across verified CUE/BIN and CHD container layouts, using exact extracted boot-code fingerprints bound to the published native build. Different executable revisions remain rejected until rebuilt and reviewed. Verified container-layout profiles cover 132 of 164 published game identities with 369 executable fingerprints; the remaining 32 keep exact-disc matching only. The third-party reported disc has not been directly tested. Existing disc images, BIOS, game code, game configuration, saves and settings are preserved. This is an online application/player wrapper update; no full game archive or native executable is replaced. Keeps True Color, PAL support, save states, error export, community review and the three separate public program choices.


## Public Remaker CHD support

The public Remaker now includes its licensed Windows x64 CHD decoder, so a fresh complete Remaker ZIP can inspect supported owner-selected CHD discs without an external decoder path or private installation. Both Remaker downloads include the required decoder and license notices. The separate Player component retains its existing approved wrapper-only inventory. Private Remaker 0.20.6 also fixes loading its trusted player-template identity helper on a clean installation. This update also preserves verified container matching for 132 of 164 published game identities; 32 still require an exact disc match. Different game-code revisions remain refused until rebuilt/reviewed. No BIOS, disc images, game assets or native game executables are included or changed. Existing saves, settings and custom update feeds are preserved. The third-party reported disc remains untested.


## Self-contained Player CHD support

Adds self-contained CHD selection and playback preparation to the public and private PS1 Player, using a pinned licensed decoder bundled in approved wrapper files. Supported owner-selected CHDs no longer depend on an external decoder path or a private Remaker installation. Existing CUE/BIN workflows, exact native-code revision checks, saves, settings and update feeds are preserved. The public Remaker downloads retain their licensed built-in CHD decoder and trusted-template import fix. Container matching retains 132 verified profiles across 164 published identities; 32 remain exact-disc-only. No BIOS, original disc images or native game executables are included or replaced. The third-party reported disc remains untested.


## Multi-disc Player setup

Improves public and private Player multi-disc setup: add matching discs together, then select a configured disc after boot once the native tray API is confirmed. Curated fallback definitions cover six families and fourteen approved native identities; other titles require matching package-provided metadata. Boot roles remain distinct: switching a mounted disc does not restart another story or turn Gran Turismo Arcade into Simulation. Includes reviewed loopback disc-control host sources for future Remaker builds and generates exact local disc-set metadata for verified curated sources. Existing private native builds may require Update Port/rebuild; a Player update alone cannot add a missing native API. Separately reviewed public game patches supply native runtime updates where required. Keeps exact roster checks, self-contained licensed CHD decoding and retained temporary files through owned game exit or Stop. No external decoder is required. Different game-code revisions remain rejected. This application update preserves installed game executables, BIOS, discs, saves and settings; no universal multi-disc or full-gameplay claim is made. Public game update 1.0.2 migrates fourteen specifically reviewed native runtime builds while retaining exact original guest-code and disc identity protections; original full-download archives remain unchanged. Actual Driver 2 swaps used a freshly built stock ABI2 BIOS helper. Alone in the Dark wrapper/swap validation used a documented scratch-only existing ABI1 BIOS fixture: this update does not establish that fresh ABI1 BIOS-helper generation is fixed, and no fixture or BIOS is distributed. For an existing website game download, close the game and Player, then run its Start-Update.cmd online updater to receive the game-specific runtime patch. Update program inside the standalone Player updates the shared Player, not an installed game executable.


## Display, fullscreen and High Performance builds

Adds a saved Display dithering control in the shared Remaker and Player Display panels for every game, with real renderer capability checks. Remaker Display now reads and saves the same effective display settings as the Player, including stale native-INI overrides, while preserving unrelated settings. Saved fullscreen modes use the native game window, while Windowed can remain embedded. The Separate game window preference is preserved. The forwarded customer startup behavior has not been independently reproduced; the saved-mode routing and stale-override defects are independently verified. High Performance builds replace the fixed two-worker limit with a memory-bounded budget targeting up to 95% of logical CPU workers, applied to both CMake and AOT generation. The app-wide choice is saved. This controls useful CPU compilation work; exact CPU utilization or GPU compilation utilization is not guaranteed. Public game update 1.0.3 is cumulative: the same fourteen previously reviewed 1.0.2 native runtime files are included unchanged so players can skip older updates safely; no native rebuild or new native hashes are introduced. Original full-game downloads, BIOS, discs, saves, settings and game identities are preserved. Free-camera/right-stick gameplay camera work and extended draw distance require verified game-specific hooks behind any shared Player controls; no universal camera or distance feature is claimed. Existing ABI1 fresh-helper and full-campaign validation limits remain unchanged.


## Experimental Akuji scene controls

Adds shared Gameplay scene controls to both Players, with Original defaults and exact native/profile verification. Experimental Akuji (USA, SLUS-00715) support provides a detached right-stick free camera, extended world draw distance and enhanced adaptive geometry subdivision. Other games retain their original behavior. This is adaptive geometry detail, not new authored models or universal LOD. Pause, unsupported scenes and successful state restores reset scene enhancements. New scene-native user and internal states are profile-bound and safely refused by older runtimes; legacy saves remain readable. The verified native game update is distributed separately. Application packages contain no game native, generated retail shards, BIOS, discs or player data. Existing batch completed-build checks, queue cleanup, error export, CHD, multidisc, display and updater behavior are retained. Validation covers the tested Akuji mission, near clipping, shared controls and isolated public/private launches. Full-campaign and physical-controller validation are not claimed; warm ABI1 BIOS-preparation fixture limitations remain.

