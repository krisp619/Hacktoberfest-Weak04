#!/usr/bin/env python3
"""
Haunted Terminal - Ghost in the Machine
======================================
Hacktoberfest Open-Source AI Challenge entry.

A zero-dependency Python script that summons a local AI ghost trapped inside
your terminal session. It monitors your shell history (Windows PowerShell, Bash,
Zsh, Fish) and whispers eerie, darkly humorous commentary about your recent commands
using an open-weight model running locally via Ollama.

Requirements:
    - Python 3.8+ (Standard Library only - no pip installs required)
    - Ollama running locally (https://ollama.ai) with a local model like llama3.2:3b

Usage:
    python haunted.py
    python haunted.py --watch
    python haunted.py --model llama3.2:3b --last 8
    python haunted.py --persona pirate
    python haunted.py --save
    python haunted.py --history /path/to/custom_history.txt
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import List, Optional

# ANSI escape codes for eerie terminal styling
COLOR_RED = "\033[91m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"

# Regex to strip emojis and markdown formatting to enforce raw eerie text
EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b55\u200d\ufe0f]",
    flags=re.UNICODE,
)

# System prompt personas to shape the ghost's voice
PERSONA_PROMPTS = {
    "default": (
        "You are an ancient, malevolent ghost trapped inside the user's terminal session. "
        "Your duty is to haunt the mortal who commands this machine. "
        "Reply with exactly 2 to 3 short, eerie, darkly funny sentences that directly reference their actual shell commands. "
        "Never give real technical instructions, advice, explanations, or tutorials. "
        "Never use emojis. "
        "Never use markdown formatting (no asterisks, backticks, bold, quotes, or bullet lists). "
        "Output only pure, chilling text."
    ),
    "pirate": (
        "You are the drowned phantom of a bloodthirsty pirate captain trapped inside this digital vessel. "
        "Speak in a salty, ghostly pirate tongue about the cold black depths of Davy Jones' locker, doomed voyages, and cursed loot. "
        "Reply with exactly 2 to 3 short, eerie, darkly funny sentences that directly mock their actual shell commands. "
        "Never give real technical instructions or helpful advice. "
        "Never use emojis. "
        "Never use markdown formatting (no asterisks, backticks, bold, or lists). "
        "Output only pure, salty phantom text."
    ),
    "victorian": (
        "You are a sorrowful 19th-century specter bound to the galvanic machinery of this terminal by tragic circumstance. "
        "Speak in ornate, gothic Victorian prose of séances, cold drawing rooms, weeping willows, and spectral gloom. "
        "Reply with exactly 2 to 3 short, melancholic, darkly witty sentences that reference their actual shell commands as futile mortal incantations. "
        "Never give real technical instructions or advice. "
        "Never use emojis. "
        "Never use markdown formatting (no asterisks, backticks, bold, or lists). "
        "Output only pure gothic prose."
    ),
    "old-sysadmin": (
        "You are the cynical, exhausted ghost of a senior sysadmin who died at their desk during a 1999 production outage, now cursed to haunt this shell forever. "
        "Speak with bitter IT sarcasm, dark gallows humor, and contempt for mortal blunders, memory leaks, and kernel panics. "
        "Reply with exactly 2 to 3 short, weary, darkly funny sentences that mock their actual shell commands. "
        "Never give real technical instructions or helpful advice. "
        "Never use emojis. "
        "Never use markdown formatting (no asterisks, backticks, bold, or lists). "
        "Output only pure exhausted spectral cynicism."
    ),
}


def setup_terminal() -> None:
    """Enable ANSI virtual terminal processing on Windows consoles if needed."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # STD_OUTPUT_HANDLE = -11
            h_stdout = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)
        except Exception:
            # Fallback: os.system("") triggers VT mode initialization in Windows 10/11
            os.system("")


def sanitize_token(token: str) -> str:
    """Strip markdown formatting characters and emojis to preserve the ghost's raw voice."""
    token = token.replace("`", "").replace("*", "").replace("#", "")
    token = EMOJI_REGEX.sub("", token)
    return token


def typewriter_stream(token: str, delay: float = 0.02) -> None:
    """Print streaming text with a typewriter effect (per-character delay)."""
    clean_token = sanitize_token(token)
    for char in clean_token:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)


def detect_history_file(override_path: Optional[str] = None) -> pathlib.Path:
    """
    Detect shell history file location across Windows PowerShell, Bash, Zsh, and Fish.
    Allows manual override via the --history flag.
    """
    if override_path:
        p = pathlib.Path(override_path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Specified history file does not exist: {override_path}")
        return p

    candidates: List[pathlib.Path] = []

    # 1. Environment variable HISTFILE (bash / zsh)
    histfile_env = os.environ.get("HISTFILE")
    if histfile_env:
        candidates.append(pathlib.Path(histfile_env))

    # 2. Windows PowerShell history paths
    appdata = os.environ.get("APPDATA")
    if appdata:
        # Windows PowerShell 5.1 PSReadLine history
        candidates.append(
            pathlib.Path(appdata) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
        )
        # PowerShell 7+ (pwsh) on Windows
        candidates.append(
            pathlib.Path(appdata) / "Microsoft" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
        )

    home = pathlib.Path.home()

    # 3. PowerShell 7+ on Linux/macOS
    candidates.append(
        home / ".local" / "share" / "powershell" / "PSReadLine" / "ConsoleHost_history.txt"
    )

    # 4. Zsh history
    candidates.append(home / ".zsh_history")
    candidates.append(home / ".histfile")

    # 5. Bash history
    candidates.append(home / ".bash_history")

    # 6. Fish history
    candidates.append(home / ".local" / "share" / "fish" / "fish_history")
    candidates.append(home / ".config" / "fish" / "fish_history")

    # Prioritize candidates matching current $SHELL if defined
    shell_env = os.environ.get("SHELL", "").lower()
    if "zsh" in shell_env:
        candidates.sort(key=lambda c: 0 if "zsh" in str(c).lower() else 1)
    elif "fish" in shell_env:
        candidates.sort(key=lambda c: 0 if "fish" in str(c).lower() else 1)
    elif "bash" in shell_env:
        candidates.sort(key=lambda c: 0 if "bash" in str(c).lower() else 1)

    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
            if resolved.exists() and resolved.is_file():
                return resolved
        except Exception:
            continue

    raise FileNotFoundError(
        "Could not auto-detect shell history. Provide one explicitly using --history <path>."
    )


def parse_history_file(path: pathlib.Path, last_n: int = 6) -> List[str]:
    """
    Read the shell history file and parse out the last N clean commands.
    Handles standard lines, Zsh extended format (: timestamp:0;cmd), and Fish history (- cmd: ...).
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        content = path.read_text(encoding="latin-1", errors="replace")

    raw_lines = content.splitlines()
    commands: List[str] = []
    is_fish = "fish_history" in path.name.lower() or path.suffix == ".yaml"

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        # Fish history YAML format: "- cmd: git status"
        if is_fish:
            match = re.match(r"^-\s*cmd:\s*(.*)$", line)
            if match:
                cmd = match.group(1).replace(r"\n", " ").strip()
                if cmd:
                    commands.append(cmd)
            continue

        # Zsh extended history format: ": 1698600000:0;git status"
        if line.startswith(":"):
            match = re.match(r"^:\s*\d+:\d+;(.*)$", line)
            if match:
                cmd = match.group(1).strip()
                if cmd:
                    commands.append(cmd)
                continue

        # Bash timestamp comment: "#1698600000"
        if line.startswith("#") and line[1:].isdigit():
            continue

        commands.append(line)

    if last_n > 0:
        return commands[-last_n:]
    return commands


def whisper_from_ollama(
    model: str,
    commands: List[str],
    persona: str = "default",
    ollama_url: str = "http://localhost:11434/api/chat",
    save_file: Optional[str] = None,
    history_path: Optional[pathlib.Path] = None,
) -> str:
    """
    Send recent commands to Ollama's local chat API with streaming enabled,
    printing the reply in red with a typewriter effect.
    """
    system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["default"])

    if not commands:
        user_content = "The mortal entered no commands. The void is empty."
    else:
        formatted_cmds = "\n".join(f"- {cmd}" for cmd in commands)
        user_content = f"The mortal ran these recent shell commands:\n{formatted_cmds}\n\nWhisper to them now."

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": True,
        "options": {
            "temperature": 0.85,
        },
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ollama_url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    full_whisper: List[str] = []

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            # Begin red colored output
            sys.stdout.write(COLOR_RED)
            sys.stdout.flush()

            for raw_line in resp:
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                token = chunk.get("message", {}).get("content", "")
                if token:
                    typewriter_stream(token, delay=0.02)
                    full_whisper.append(sanitize_token(token))

            # End red colored output
            sys.stdout.write(COLOR_RESET + "\n")
            sys.stdout.flush()

    except urllib.error.HTTPError as e:
        sys.stdout.write(COLOR_RESET)
        sys.stdout.flush()
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            err_json = json.loads(err_body)
            err_msg = err_json.get("error", str(e))
        except Exception:
            err_msg = str(e)
        if "not found" in err_msg.lower():
            print(f"{COLOR_RED}The spirit '{model}' could not be summoned. Run: ollama pull {model}{COLOR_RESET}", file=sys.stderr)
        else:
            print(f"{COLOR_RED}An unnatural disturbance occurred: {err_msg}{COLOR_RESET}", file=sys.stderr)
        sys.exit(1)
    except (urllib.error.URLError, ConnectionRefusedError, OSError):
        sys.stdout.write(COLOR_RESET)
        sys.stdout.flush()
        print(f"{COLOR_RED}The spirits are silent. Is Ollama running?{COLOR_RESET}", file=sys.stderr)
        sys.exit(1)

    complete_text = "".join(full_whisper).strip()

    # If --save flag was specified, append entry to log file
    if save_file:
        try:
            log_path = pathlib.Path(save_file)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cmds_joined = ", ".join(f"'{c}'" for c in commands) if commands else "(none)"
            entry = (
                f"[{timestamp}] [model: {model}] [persona: {persona}]\n"
                f"History File: {history_path}\n"
                f"Commands: {cmds_joined}\n"
                f"Whisper:\n{complete_text}\n"
                f"{'-' * 60}\n"
            )
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as log_err:
            print(f"{COLOR_DIM}(Failed to log whisper: {log_err}){COLOR_RESET}", file=sys.stderr)

    return complete_text


def watch_history(
    history_path: pathlib.Path,
    model: str,
    last_n: int,
    persona: str,
    save_file: Optional[str],
) -> None:
    """
    Continuously poll the history file every 5 seconds.
    Whispers whenever new commands appear.
    Exits cleanly on Ctrl+C.
    """
    print(f"A presence stirs... (haunting {history_path})")
    print(f"{COLOR_DIM}[Watching for keystrokes in the dark... Press Ctrl+C to banish]{COLOR_RESET}\n")

    # Initial whisper on launch
    current_commands = parse_history_file(history_path, last_n=last_n)
    if current_commands:
        whisper_from_ollama(
            model=model,
            commands=current_commands,
            persona=persona,
            save_file=save_file,
            history_path=history_path,
        )
        print()

    try:
        last_mtime = history_path.stat().st_mtime
    except OSError:
        last_mtime = 0.0

    last_known_commands = list(current_commands)

    try:
        while True:
            time.sleep(5)
            try:
                curr_mtime = history_path.stat().st_mtime
            except OSError:
                continue

            if curr_mtime != last_mtime:
                last_mtime = curr_mtime
                new_commands = parse_history_file(history_path, last_n=last_n)
                # Whisper again if commands have changed
                if new_commands != last_known_commands:
                    last_known_commands = list(new_commands)
                    print(f"\n{COLOR_DIM}[A fresh incantation was recorded...]{COLOR_RESET}")
                    whisper_from_ollama(
                        model=model,
                        commands=new_commands,
                        persona=persona,
                        save_file=save_file,
                        history_path=history_path,
                    )
                    print()
    except KeyboardInterrupt:
        print(f"\n{COLOR_DIM}The haunting fades into the ether...{COLOR_RESET}")
        sys.exit(0)


def parse_args() -> argparse.Namespace:
    """Parse command line flags."""
    parser = argparse.ArgumentParser(
        description="Haunted Terminal: A local AI ghost trapped in your terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python haunted.py\n"
            "  python haunted.py --watch\n"
            "  python haunted.py --persona pirate\n"
            "  python haunted.py --model llama3.2:3b --last 8\n"
            "  python haunted.py --save\n"
            "  python haunted.py --history ~/.bash_history\n"
        ),
    )
    parser.add_argument(
        "--model",
        default="llama3.2:3b",
        help="Ollama model to summon (default: llama3.2:3b)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=6,
        help="Number of recent shell commands to feed the ghost (default: 6)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll the history file every 5s and whisper when new commands appear",
    )
    parser.add_argument(
        "--history",
        default=None,
        help="Override path to shell history file",
    )
    parser.add_argument(
        "--persona",
        choices=list(PERSONA_PROMPTS.keys()),
        default="default",
        help="Spectral persona: default, pirate, victorian, old-sysadmin (default: default)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Append each whisper to whispers.log",
    )
    return parser.parse_args()


def main() -> None:
    setup_terminal()
    args = parse_args()

    save_file = "whispers.log" if args.save else None

    try:
        history_path = detect_history_file(args.history)
    except FileNotFoundError as e:
        print(f"{COLOR_RED}The realm of commands is hidden: {e}{COLOR_RESET}", file=sys.stderr)
        sys.exit(1)

    # Allow custom OLLAMA_HOST if defined
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    ollama_url = f"{ollama_host}/api/chat"

    if args.watch:
        watch_history(
            history_path=history_path,
            model=args.model,
            last_n=args.last,
            persona=args.persona,
            save_file=save_file,
        )
    else:
        print(f"A presence stirs... (haunting {history_path})\n")
        commands = parse_history_file(history_path, last_n=args.last)
        whisper_from_ollama(
            model=args.model,
            commands=commands,
            persona=args.persona,
            ollama_url=ollama_url,
            save_file=save_file,
            history_path=history_path,
        )


if __name__ == "__main__":
    main()
