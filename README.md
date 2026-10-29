# 👻 Haunted Terminal

> *"A digital phantom trapped inside your machine, watching every keystroke in the dark."*

Built for the **Hacktoberfest Open-Source AI Challenge** (Theme: **"Ghost in the Machine"**).

**Haunted Terminal** is a lightweight, zero-dependency Python tool that awakens an eerie spectral presence trapped inside your terminal session. It monitors your shell history across Windows PowerShell, Bash, Zsh, and Fish, feeding your recent commands into an open-weight model running 100% locally through [Ollama](https://ollama.ai).

The ghost streams haunting, darkly funny commentary back into your console in vivid spectral red, character by character, mocking your mortal command-line endeavors.

---

## ✨ Features

- 🔒 **100% Local & Private:** No cloud APIs, no telemetry, no API keys, no tracking. Your shell history never leaves your machine.
- 🐍 **Zero Dependencies:** Pure Python 3.8+ standard library only (`urllib`, `json`, `argparse`). No `pip install` required.
- 🐚 **Cross-Platform Shell History Detection:** Automatically discovers your active shell history:
  - **Windows PowerShell / PowerShell 7+** (`%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`)
  - **Zsh** (`~/.zsh_history`, including extended `: timestamp:0;cmd` format parsing)
  - **Bash** (`~/.bash_history` & `$HISTFILE`)
  - **Fish** (`~/.local/share/fish/fish_history` YAML format)
- 🔴 **Spectral Typewriter Display:** Streaming output in ANSI red with typewriter pacing.
- 👁️ **Watch Mode (`--watch`):** Silently waits in the background, awakening with a fresh whisper whenever you enter new shell commands.
- 🎭 **Multiple Personas (`--persona`):** Choose the voice of your apparition: `default`, `pirate`, `victorian`, or `old-sysadmin`.
- 📜 **Whisper Logging (`--save`):** Persist haunting transcripts to `whispers.log`.

---

## 🚀 Quick Setup

### 1. Install Ollama
Download and install Ollama from [ollama.com](https://ollama.com) (available for Windows, macOS, and Linux).

### 2. Pull the Open Model
Pull the default lightweight open model:
```bash
ollama pull llama3.2:3b
```
*(You can also use any other model like `mistral`, `qwen2.5:7b`, `phi3:mini`, etc.)*

### 3. Run Haunted Terminal
Clone or download this repository, then run:
```bash
python haunted.py
```

---

## 🕹️ Usage & Flag Reference

### Basic Invocation
Summon the ghost once based on your last 6 shell commands:
```bash
python haunted.py
```

### Watch Mode (`--watch`)
Leave the ghost lingering in a side terminal window. Every 5 seconds, it checks your shell history and whispers new commentary whenever you execute commands:
```bash
python haunted.py --watch
```
*Press `Ctrl+C` at any time to banish the ghost and exit cleanly.*

### Spectral Personas (`--persona`)
Transform the ghost's dialect and personality:
- `default`: The classic trapped digital apparition.
- `pirate`: A drowned sea captain haunting the digital depths of Davy Jones' locker.
- `victorian`: An ornate, melancholic 19th-century spirit bound to the galvanic machine.
- `old-sysadmin`: A cynical sysadmin who died at their desk during a 1999 outage.

```bash
# Summon the drowned pirate captain
python haunted.py --persona pirate

# Summon the Victorian gothic spirit
python haunted.py --persona victorian

# Summon the cynical 1999 sysadmin
python haunted.py --persona old-sysadmin
```

### Custom History Depth (`--last`)
Feed more or fewer commands to the entity (default is 6):
```bash
python haunted.py --last 10
```

### Swapping Models (`--model`)
Run any open-weight LLM supported by your local Ollama instance:
```bash
python haunted.py --model mistral
python haunted.py --model qwen2.5:7b
python haunted.py --model phi3
```

### Override History File (`--history`)
Specify a custom or non-standard shell history path:
```bash
python haunted.py --history ~/.bash_history
python haunted.py --history "C:\Users\username\custom_history.txt"
```

### Save Whispers (`--save`)
Append every apparition whisper with timestamps and command history to `whispers.log`:
```bash
python haunted.py --save
python haunted.py --watch --persona pirate --save
```

---

## 🌐 Why Open?

Why does Haunted Terminal rely strictly on open-weight local AI?

1. **Your Shell History Stays Private:**
   Shell history frequently contains sensitive data—private paths, internal hostnames, repository names, and parameter tokens. Sending raw shell history to remote cloud APIs poses severe privacy risks. By running models locally with Ollama, **zero bytes ever leave your device**.
2. **Works 100% Offline:**
   Whether you are on a plane, commuting, or enduring a network blackout, Haunted Terminal runs entirely off local compute.
3. **No Fees or API Keys:**
   No rate limits, no subscriptions, and no surprise billing. The code and model are yours forever.
4. **Swappable Architecture:**
   You aren't locked into a single proprietary vendor. You can switch between Llama, Mistral, Qwen, Gemma, or custom fine-tuned weights with a simple `--model` flag.

---

## 🧪 Spooky Error Handling

If Ollama is not running when the script runs, Haunted Terminal catches the connection failure cleanly and outputs:

```
The spirits are silent. Is Ollama running?
```

Simply start Ollama (`ollama serve`) and invoke the script again.

---

## 📄 License

This project is open-source under the terms of the [MIT License](LICENSE).
Feel free to fork, hack, and haunt your own terminals.
