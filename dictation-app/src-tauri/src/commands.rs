use crate::config_io;
use serde_json::Value;

#[tauri::command]
pub fn read_config() -> Result<Value, String> {
    config_io::read_config()
}

#[tauri::command]
pub fn save_config(config: Value) -> Result<(), String> {
    config_io::write_config(&config)
}

#[tauri::command]
pub fn read_api_key() -> Result<String, String> {
    config_io::read_api_key()
}

#[tauri::command]
pub fn save_api_key(key: String) -> Result<(), String> {
    config_io::write_api_key(&key)
}

#[tauri::command]
pub async fn validate_api_key(key: String) -> Result<bool, String> {
    let client = reqwest::Client::new();
    let resp = client
        .get("https://api.openai.com/v1/models")
        .bearer_auth(&key)
        .send()
        .await
        .map_err(|e| format!("request failed: {e}"))?;
    Ok(resp.status().is_success())
}

#[tauri::command]
pub fn save_config_field(key: String, value: Value) -> Result<(), String> {
    let mut config = config_io::read_config()?;
    if let Some(obj) = config.as_object_mut() {
        obj.insert(key, value);
    }
    config_io::write_config(&config)
}
