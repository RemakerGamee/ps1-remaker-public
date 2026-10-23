# RetroRemakes PS1 Remaker

Public beta **v0.20.0-public-beta** — Windows Studio and Player for experimental native PS1 projects.

Download the public ZIP from this repository's **Releases** section. Extract the entire archive; Python 3.11+ with Tcl/Tk is required. Start `Start-PS1-Remaker.cmd` for Studio or `Start-PS1-Player.cmd` for Player. Building projects also requires a compatible C++ toolchain, CMake and Windows SDK.

You must supply your own supported PS1 BIOS and game disc files. No BIOS or games are included. Building a game does not guarantee compatibility. Windows execution, physical controllers and commercial-game gameplay remain unverified for this public edition.

The package includes the public Studio and Player source, bundled tools, license terms, third-party notices, engine provenance and verification report. The bundled PSXRecomp engine uses the PolyForm Noncommercial license; see the complete terms inside the ZIP. This is a free noncommercial public beta.

## PS1 game players

The [game catalog](games/README.md) lists the 164 reviewed game projects from the website. GitHub release downloads appear as verified mirroring completes; the initial mirror is currently in progress. Every refreshed game ZIP includes `Start-Update.cmd` for fixes matched to its exact disc revision. Game project releases are separate from the public Studio/Player ZIP; users still supply their original disc and supported BIOS. Game inclusion does not guarantee gameplay compatibility.

Online updates download and verify a release before installation. Installation-specific locks allow unrelated games and Studio installations to keep running. Saves, settings, disc/BIOS paths and mods are protected from update targets. Shared Player fixes and game-specific fixes use separate feeds; neither automatically proves compatibility.
