use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to OAgent.", name)
}

#[tauri::command]
fn get_app_info() -> serde_json::Value {
    serde_json::json!({
        "name": "OAgent",
        "version": "0.1.0",
        "description": "Open-source pluggable universal Agent framework"
    })
}

#[tauri::command]
async fn start_backend(app_handle: tauri::AppHandle) -> Result<(), String> {
    // In production, you might want to start the Python backend here
    // For development, the backend runs separately
    println!("Backend starting...");
    Ok(())
}

#[tauri::command]
async fn stop_backend() -> Result<(), String> {
    println!("Backend stopping...");
    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            get_app_info,
            start_backend,
            stop_backend
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}