use tauri::command;
use dirs::document_dir;
use serde::{Serialize, Deserialize};
use serde_json::Value as JsonValue;
use tempfile::NamedTempFile;
use std::{fs, path::{Path, PathBuf}, process::Command, time::{SystemTime, UNIX_EPOCH}};
use base64::{engine::general_purpose, Engine as _};


#[derive(Serialize)]
struct CommandOutput {
    stdout: String,
    stderr: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SelectedMetricsBySensor {
    chromeleon_offline: Vec<String>,
    chromeleon_online: Vec<String>,
    pigna: Vec<String>,
}


const SCRIPT_PATH: &str = "/home/lucaslhm/Documents/ETIC/Bobine/project/desktop_app/src-tauri/python-scripts/main.py";

/// ---------- Helper générique pour appeler Python ----------

fn run_python(args: &[&str]) -> Result<CommandOutput, String> {
    let output = Command::new("python3")
        .arg("-u") // <<< important : stdout/stderr non-bufferisés
        .arg(SCRIPT_PATH)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e))?;

    let stdout = String::from_utf8(output.stdout)
        .map_err(|e| format!("Invalid UTF-8 in stdout: {}", e))?;
    let stderr = String::from_utf8(output.stderr)
        .map_err(|e| format!("Invalid UTF-8 in stderr: {}", e))?;

    if !output.status.success() {
        return Err(if stderr.trim().is_empty() {
            "Python exited with error".into()
        } else {
            stderr
        });
    }

    if stdout.trim().is_empty() && !stderr.trim().is_empty() {
        return Err(stderr);
    }

    Ok(CommandOutput { stdout, stderr })
}

fn parse_python_json(stdout: &str) -> Result<JsonValue, String> {
    if stdout.trim().is_empty() {
        return Err("Empty stdout from Python".into());
    }
    let v: JsonValue = serde_json::from_str(stdout)
        .map_err(|e| format!("Failed to parse JSON from Python stdout: {e}\nRaw: {stdout}"))?;

    if let Some(err) = v.get("error") {
        return Err(err.as_str().unwrap_or("Unknown error").to_string());
    }
    Ok(v.get("result").cloned().unwrap_or(v))
}

/// ---------- Commandes par action ----------

#[tauri::command]
fn context_is_correct(dir_path: String) -> Result<bool, String> {
    let out = run_python(&["CONTEXT_IS_CORRECT", &dir_path])?;
    let json = parse_python_json(&out.stdout)?;
    // Python renvoie {"result": true/false}
    json.as_bool()
        .ok_or_else(|| "Invalid JSON: expected boolean".into())
}

#[tauri::command]
fn get_context_masses(dir_path: String) -> Result<JsonValue, String> {
    let out = run_python(&["GET_CONTEXT_MASSES", &dir_path])?;
    if out.stdout.trim().is_empty() {
        return Err(if out.stderr.trim().is_empty() {
            "Empty stdout from Python".into()
        } else {
            out.stderr
        });
    }
    let json = parse_python_json(&out.stdout)?;
    json.as_object()
        .map(|obj| {serde_json::to_value(obj).unwrap()})
        .ok_or_else(|| "Invalid JSON: expected object".into())
    
}

#[tauri::command]
fn get_context_b64(dir_path: String) -> Result<String, String> {
    let out = run_python(&["GET_CONTEXT_B64", &dir_path])?;
    if out.stdout.trim().is_empty() {
        return Err(if out.stderr.trim().is_empty() {
            "Empty stdout from Python".into()
        } else {
            out.stderr
        });
    }
    let json = parse_python_json(&out.stdout)?;
    json.as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| "Invalid JSON: expected string".into())
}

#[tauri::command]
fn get_graphs_available(dir_path: String) -> Result<JsonValue, String> {
    let out = run_python(&["GET_GRAPHS_AVAILABLE", &dir_path])?;
    if out.stdout.trim().is_empty() {
        return Err(if out.stderr.trim().is_empty() {
            "Empty stdout from Python".into()
        } else {
            out.stderr
        });
    }
    parse_python_json(&out.stdout)
}


#[tauri::command]
async fn generate_and_save_excel(
    dir_path: String,
    metric_wanted: SelectedMetricsBySensor,
    destination_path: String,
) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        let metrics_json = serde_json::to_string(&metric_wanted)
            .map_err(|e| format!("Failed to serialize metrics: {e}"))?;
        let out = run_python(&["GENERATE_EXCEL_TO_FILE", &metrics_json, &dir_path, &destination_path])?;
        // on peut parser/valider si besoin
        Ok::<(), String>(())
    })
    .await
    .map_err(|e| format!("Join error: {e}"))??;
    Ok(())
}


/// ---------- Utilitaires fichier / système ----------

#[command]
fn get_documents_dir() -> Result<String, String> {
    document_dir()
        .ok_or_else(|| "Impossible de récupérer le dossier Documents".into())
        .map(|p| p.to_string_lossy().into_owned())
}

#[command]
fn remove_dir(dir_path: String) -> Result<(), String> {
    if Path::new(&dir_path).exists() {
        fs::remove_dir_all(&dir_path)
            .map_err(|e| format!("Erreur suppression répertoire : {}", e))?;
    }
    Ok(())
}

#[command]
fn write_file(destination_path: String, contents: Vec<u8>) -> Result<(), String> {
    if let Some(parent) = Path::new(&destination_path).parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Erreur création répertoire : {}", e))?;
    }
    fs::write(&destination_path, contents)
        .map_err(|e| format!("Erreur lors de l'écriture : {}", e))?;
    println!("✅ Écriture de `{}` réussie", destination_path);
    Ok(())
}

#[command]
fn copy_file(source_path: String, destination_path: String) -> Result<(), String> {
    if let Some(parent) = Path::new(&destination_path).parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Erreur création répertoire : {}", e))?;
    }
    fs::copy(&source_path, &destination_path)
        .map_err(|e| format!("Erreur lors de la copie : {}", e))?;
    println!("✅ Copie de `{}` vers `{}` réussie", source_path, destination_path);
    Ok(())
}

#[command]
fn my_custom_command(invoke_message: String) {
    println!("I was invoked from JavaScript, with this message: {}", invoke_message);
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            // Python actions exposées une par une :
            context_is_correct,
            get_context_masses,
            get_context_b64,
            get_graphs_available,
            generate_and_save_excel,
            // utilitaires :
            get_documents_dir,
            write_file,
            copy_file,
            my_custom_command,
            remove_dir
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
