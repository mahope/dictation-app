# dictation-app

System-wide dictation tool for Windows. Press a hotkey to record, press again to stop — the transcription is pasted into the active text field.

## Usage

```
python dictation.py
```

A small pill-shaped overlay appears in the top-right corner of the screen:

- **Grey** — idle, ready to record
- **Red (pulsing) "REC"** — recording
- **Amber (animated dots)** — transcribing

The overlay never steals focus from your active window.

## Hotkey

`Ctrl+Shift+D` — toggle recording on/off

## Language

Supports both **Danish** and **English** — speak in either language and the transcription follows automatically.

## Model

`gpt-4o-transcribe` via the OpenAI API.

## Configuration

Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`.

## Quit

Press `Ctrl+C` in the terminal, or close the terminal window.
