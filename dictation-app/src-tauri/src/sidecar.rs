use std::sync::Mutex;
use tauri::async_runtime::spawn;
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

pub struct SidecarState {
    pub child: Mutex<Option<CommandChild>>,
}

fn data_dir() -> String {
    if cfg!(debug_assertions) {
        // dev mode – repo root is two levels up from src-tauri/
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_default()
    } else {
        // prod – use %APPDATA%\Dictation (same as config_io)
        let dir = dirs::config_dir()
            .unwrap_or_else(|| std::path::PathBuf::from("."))
            .join("Dictation");
        let _ = std::fs::create_dir_all(&dir);
        dir.to_string_lossy().to_string()
    }
}

pub fn spawn_sidecar(app: &AppHandle) -> Result<(), String> {
    let shell = app.shell();
    let dir = data_dir();
    let (mut rx, child) = shell
        .sidecar("dictation-engine")
        .map_err(|e| format!("sidecar command: {e}"))?
        .args(["--headless", "--data-dir", &dir])
        .spawn()
        .map_err(|e| format!("spawn sidecar: {e}"))?;

    // Store child handle for stdin writes and cleanup
    let state = app.state::<SidecarState>();
    *state.child.lock().unwrap() = Some(child);

    // Forward stdout JSON events to webview
    let handle = app.clone();
    spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let line = String::from_utf8_lossy(&line);
                    let line = line.trim();
                    if !line.is_empty() {
                        if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(line) {
                            let _ = handle.emit("sidecar-event", &parsed);
                        }
                    }
                }
                CommandEvent::Stderr(line) => {
                    let line = String::from_utf8_lossy(&line);
                    eprintln!("[engine] {}", line.trim());
                }
                CommandEvent::Terminated(status) => {
                    eprintln!("[engine] terminated: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
    });

    Ok(())
}

pub fn send_to_sidecar(app: &AppHandle, msg: &str) -> Result<(), String> {
    let state = app.state::<SidecarState>();
    let mut guard = state.child.lock().unwrap();
    if let Some(child) = guard.as_mut() {
        child
            .write((msg.to_string() + "\n").as_bytes())
            .map_err(|e| format!("write stdin: {e}"))
    } else {
        Err("sidecar not running".to_string())
    }
}

pub fn kill_sidecar(app: &AppHandle) {
    let state = app.state::<SidecarState>();
    let mut guard = state.child.lock().unwrap();
    if let Some(child) = guard.take() {
        let _ = child.kill();
    }
}
