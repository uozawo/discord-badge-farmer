<p align="center">
  <img src="assets/banner.png" alt="Discord Badge Farmer" width="100%">
</p>

A small Windows script that grows Discord's **Game Variety** badge (Sampler → … → Universalist, 100+ games) by running dummy executables that the Discord desktop app detects as real games.

## Results

<p align="center">
  <img src="assets/universalist.png" width="320" alt="Universalist badge, 129 games played">
</p>

<p align="center"><b>Universalist</b>: 129 games, unlocked in about two days.</p>

## How it works

1. Downloads Discord's public list of detectable games (`/api/v9/applications/detectable`).
2. Builds a tiny, minimized window program with the C# compiler that ships with Windows (`csc.exe`).
3. Copies it under each game's expected folder and `.exe` name, then runs it.
4. Discord sees the process and reports "Playing …" for that game, one game at a time.

It doesn't read your Discord token, doesn't modify the Discord app, and doesn't touch your account directly.

## Requirements

- Windows 10 or 11 (.NET Framework 4 is installed by default)
- Python 3.8+
- Discord **desktop** app, open and signed in

## Before you start

In Discord settings, make sure these are on:

- **Activity Privacy → Share your detected activities**
- **Data & Privacy → Use data to personalize my Discord experience** (required for the badge to count)

## Usage

```bash
# Check that detection works: runs one game until you press Enter
python discord_badge_farmer.py --test

# Full run (defaults: ~105 games, one at a time, 15 seconds each ≈ 30 minutes)
python discord_badge_farmer.py
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--games` | 105 | Number of games to run (a few extra as buffer) |
| `--batch` | 1 | Games running at once. Discord seems to count only one at a time, so keep it at 1 |
| `--seconds` | 15 | How long each game stays open. 15 seconds is enough for a game to count |
| `--test` | — | Run a single game until you press Enter |

## Notes

- **Badge progress can take 1–2 days to update.** Don't judge it by the live counter.
- To find the real minimum time per game, open DevTools in Discord (`Ctrl+Shift+I`) → Network, filter for `science`, and watch for a `running_game_heartbeat` request.
- Afterwards, delete `%USERPROFILE%\DiscordFakeGames` and clean up **Settings → Registered Games** if you like.

## Disclaimer

Faking game activity likely violates Discord's Terms of Service. It could lead to badge removal or action against your account. **Use at your own risk.** This project is not affiliated with or endorsed by Discord.
