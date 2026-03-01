mod commands;
mod config_io;
mod sidecar;

use sidecar::SidecarState;
use std::sync::Mutex;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Manager,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState {
            child: Mutex::new(None),
        })
        .setup(|app| {
            // Build tray menu
            let settings_item =
                MenuItemBuilder::with_id("settings", "Settings...").build(app)?;
            let toggle_overlay_item =
                MenuItemBuilder::with_id("toggle_overlay", "Show/Hide Overlay").build(app)?;
            let quit_item = MenuItemBuilder::with_id("quit", "Quit").build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&settings_item)
                .item(&toggle_overlay_item)
                .separator()
                .item(&quit_item)
                .build()?;

            let _tray = TrayIconBuilder::new()
                .tooltip("Dictation")
                .menu(&menu)
                .on_menu_event(move |app, event| match event.id().as_ref() {
                    "settings" => {
                        if let Some(win) = app.get_webview_window("main") {
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    }
                    "toggle_overlay" => {
                        let _ = sidecar::send_to_sidecar(
                            app,
                            r#"{"cmd":"toggle_overlay"}"#,
                        );
                    }
                    "quit" => {
                        sidecar::kill_sidecar(app);
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let tauri::tray::TrayIconEvent::DoubleClick { .. } = event {
                        let app = tray.app_handle();
                        if let Some(win) = app.get_webview_window("main") {
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    }
                })
                .build(app)?;

            // Spawn the Python sidecar engine
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = sidecar::spawn_sidecar(&handle) {
                    eprintln!("Failed to spawn sidecar: {e}");
                }
            });

            // Hide window on close instead of exiting (keep app running in tray)
            // This is handled by the Svelte frontend via onCloseRequested

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::read_config,
            commands::save_config,
            commands::save_config_field,
            commands::read_api_key,
            commands::save_api_key,
            commands::validate_api_key,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
