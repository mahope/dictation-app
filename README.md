# dictation-app

System-wide dictation tool for Windows. Press a hotkey to record, press again to stop — the transcription is pasted into the active text field.

## Usage

```
python dictation.py
```

A small equalizer overlay appears in the top-right corner of the screen (draggable):

- **Grey** — idle, ready to record
- **Red (live audio bars)** — recording
- **Amber (wave animation)** — transcribing
- **Green flash** — text pasted successfully

The overlay never steals focus from your active window. Double-click it to copy the last transcription.

## Hotkeys

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+D` | Toggle recording on/off |
| `Ctrl+Shift+Space` | Hold to record, release to stop |
| `Ctrl+Shift+H` | Show transcription history |
| `Ctrl+Shift+Escape` | Cancel current recording |

## System Tray

Right-click the tray icon for:

- Show/hide overlay
- Smart formatting toggle (punctuation cleanup via gpt-4o-mini)
- Auto-stop on silence toggle
- Microphone selection
- Start at Windows startup
- History / export / clear

## Language

Supports both **Danish** and **English** — speak in either language and the transcription follows automatically.

## Model

`gpt-4o-transcribe` via the OpenAI API, with optional `gpt-4o-mini` post-processing for punctuation and spoken commands.

## Configuration

Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`.

Settings (microphone, formatting, overlay position, etc.) are saved automatically to `config.json`.

## Quit

Right-click the tray icon and select Quit, press `Ctrl+C` in the terminal, or close the terminal window.
