use serde_json::Value;
use std::fs;
use std::path::PathBuf;

fn project_root() -> PathBuf {
    if cfg!(debug_assertions) {
        // dev mode – config.json is at repo root (two levels up from src-tauri)
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.to_path_buf())
            .unwrap_or_default()
    } else {
        // prod – use %APPDATA%\Dictation (writable user directory)
        let dir = dirs::config_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("Dictation");
        let _ = fs::create_dir_all(&dir);
        dir
    }
}

pub fn config_path() -> PathBuf {
    project_root().join("config.json")
}

pub fn env_path() -> PathBuf {
    project_root().join(".env")
}

pub fn read_config() -> Result<Value, String> {
    let path = config_path();
    let data = fs::read_to_string(&path).map_err(|e| format!("read config: {e}"))?;
    serde_json::from_str(&data).map_err(|e| format!("parse config: {e}"))
}

pub fn write_config(config: &Value) -> Result<(), String> {
    let path = config_path();
    let data =
        serde_json::to_string_pretty(config).map_err(|e| format!("serialize config: {e}"))?;
    fs::write(&path, data).map_err(|e| format!("write config: {e}"))
}

pub fn read_api_key() -> Result<String, String> {
    let path = env_path();
    let content = fs::read_to_string(&path).unwrap_or_default();
    for line in content.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("OPENAI_API_KEY=") {
            return Ok(rest.trim_matches('"').to_string());
        }
    }
    Ok(String::new())
}

pub fn write_api_key(key: &str) -> Result<(), String> {
    let path = env_path();
    let content = format!("OPENAI_API_KEY=\"{key}\"\n");
    fs::write(&path, content).map_err(|e| format!("write .env: {e}"))
}
