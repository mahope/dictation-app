# Dictation

System-wide dictation tool for Windows. Press a hotkey to record, press again to stop — the transcription is pasted into the active text field.

## Quick Start

### Option A: Standalone executable

```
python build.py
```

This creates `dist/Dictation.exe`. Place a `.env` file next to it with your `OPENAI_API_KEY` and double-click to run.

### Option B: Run from source

```
pip install -r requirements.txt
python dictation.py
```

## Setup

1. Copy `.env.example` to `.env`
2. Set your `OPENAI_API_KEY`
3. Run the app

## Overlay

A small equalizer overlay appears in the top-right corner (draggable):

- **Grey** — idle, ready to record
- **Red (live audio bars)** — recording
- **Amber (wave animation)** — transcribing
- **Green flash** — text pasted successfully

The overlay never steals focus. Double-click it to copy the last transcription.

## Hotkeys

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+D` | Toggle recording on/off |
| `Ctrl+Shift+Space` | Hold to record, release to stop |
| `Ctrl+Shift+A` | Record in append mode (add to previous) |
| `Ctrl+Shift+H` | Show transcription history |
| `Ctrl+Shift+Z` | Undo last paste |
| `Ctrl+Shift+Escape` | Cancel current recording |

## System Tray

Right-click the tray icon for:

- Show/hide overlay
- Smart formatting (punctuation cleanup via gpt-4o-mini)
- Auto-stop on silence
- Copy-only mode (no paste)
- Mute sounds
- Pin overlay position
- Overlay size (Small / Normal / Large)
- Microphone selection
- Start at Windows startup
- Log to file
- History / export / clear
- Keyboard shortcuts reference

## Language

Supports both **Danish** and **English** — speak in either language and the transcription follows automatically.

## Model

`gpt-4o-transcribe` via the OpenAI API, with optional `gpt-4o-mini` post-processing for punctuation and spoken commands.

## Configuration

All settings are saved automatically to `config.json` and persist across restarts. Transcription history is stored in `history.json` (up to 200 entries).

## Building

```
python build.py
```

Requires `pyinstaller` (`pip install pyinstaller`). Produces a single `Dictation.exe` in `dist/`.
