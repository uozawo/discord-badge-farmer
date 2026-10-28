"""
Discord detectable-game launcher (Windows only).

What it does:
  1. Downloads Discord's public list of detectable games.
  2. Compiles a tiny "do nothing" stub .exe with the C# compiler built into Windows.
  3. Copies the stub into folders that mimic each game's expected path/exe name.
  4. Launches the fakes in batches, keeps each running for a while, then closes it.

Keep Discord desktop open while it runs. Use at your own risk: this goes
against Discord's rules on manipulating features, and badges can be revoked.

Usage:
  python discord_badge_farmer.py                 # defaults below
  python discord_badge_farmer.py --games 100 --batch 10 --seconds 60
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DETECTABLE_URL = "https://discord.com/api/v9/applications/detectable"
WORK_DIR = Path.home() / "DiscordFakeGames"  # not in Temp; Discord may ignore games there
STUB_EXE = WORK_DIR / "_stub_v2.exe"

# A real (minimized) window, since detection may ignore windowless processes.
STUB_SOURCE = r"""
using System;
using System.IO;
using System.Windows.Forms;
class Stub {
    [STAThread]
    static void Main() {
        var f = new Form();
        f.Text = Path.GetFileNameWithoutExtension(Application.ExecutablePath);
        f.Width = 300; f.Height = 100;
        f.WindowState = FormWindowState.Minimized;
        Application.Run(f);
    }
}
"""


def find_csc():
    windir = os.environ.get("WINDIR", r"C:\Windows")
    for fw in ("Framework64", "Framework"):
        base = Path(windir) / "Microsoft.NET" / fw
        if base.exists():
            for v in sorted(base.glob("v4.*"), reverse=True):
                csc = v / "csc.exe"
                if csc.exists():
                    return csc
    return None


def build_stub():
    if STUB_EXE.exists():
        return
    csc = find_csc()
    if not csc:
        sys.exit("Couldn't find the .NET C# compiler (csc.exe). Is .NET Framework 4 installed?")
    src = WORK_DIR / "_stub.cs"
    src.write_text(STUB_SOURCE)
    # /target:winexe = no console window pops up for each fake game
    subprocess.run([str(csc), "/nologo", "/target:winexe", "/r:System.Windows.Forms.dll",
                    f"/out:{STUB_EXE}", str(src)], check=True)
    print("Built stub executable.")


def fetch_games():
    req = urllib.request.Request(DETECTABLE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    games = []
    for app in data:
        exes = [
            e["name"] for e in app.get("executables") or []
            if e.get("os") == "win32"
            and not e.get("is_launcher")
            and e.get("name", "").lower().endswith(".exe")
            and not e["name"].startswith(">")  # '>' entries are wildcard rules
        ]
        if exes:
            games.append((app.get("name", "?"), exes[0]))
    return games


def make_fake(exe_rel):
    # Discord matches the end of the path, so recreate the folder structure.
    target = WORK_DIR / "games" / Path(exe_rel.replace("\\", "/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(STUB_EXE, target)
    return target


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=105, help="how many games to run (a few extra as buffer)")
    p.add_argument("--batch", type=int, default=1, help="games running at the same time (1 is safest)")
    p.add_argument("--seconds", type=int, default=420, help="how long each game stays open (~7 min covers one heartbeat)")
    p.add_argument("--test", action="store_true", help="run ONE well-known game until you press Enter")
    args = p.parse_args()

    if os.name != "nt":
        sys.exit("Windows only.")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    build_stub()

    print("Fetching Discord's detectable games list...")
    games = fetch_games()

    if args.test:
        pick = next((g for g in games if g[0].lower() in ("minecraft", "terraria", "among us", "stardew valley")), games[0])
        path = make_fake(pick[1])
        proc = subprocess.Popen([str(path)], cwd=str(path.parent))
        print(f"Running '{pick[0]}' from:\n  {path}")
        print("Wait ~30 seconds, then check Settings > Registered Games in Discord.")
        input("Press Enter to stop...")
        proc.terminate()
        return
    random.shuffle(games)
    games = games[: args.games]
    print(f"Running {len(games)} games, {args.batch} at a time, {args.seconds}s per batch "
          f"(~{len(games) // args.batch * args.seconds // 60} min).")

    done = 0
    for i in range(0, len(games), args.batch):
        batch = games[i : i + args.batch]
        procs = []
        for name, exe in batch:
            try:
                path = make_fake(exe)
                procs.append(subprocess.Popen([str(path)], cwd=str(path.parent)))
                print(f"  ▶ {name}  ({exe})")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
        time.sleep(args.seconds)
        for pr in procs:
            pr.terminate()
        done += len(procs)
        print(f"Batch done — {done}/{len(games)}")
        time.sleep(3)  # give Discord a moment to register the game closing

    print("Finished. Check the badge progress in Discord (it may take a while to update).")
    print(f"You can delete {WORK_DIR} afterwards.")


if __name__ == "__main__":
    main()
