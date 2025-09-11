use tauri::{command, AppHandle, Manager};
use dirs::document_dir;
use serde::{Serialize, Deserialize};
use serde_json::Value as JsonValue;
use std::path::{Path, PathBuf};

#[derive(Serialize)]
struct CommandOutput {
    stdout: String,
    stderr: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct MetricSelected {
    name: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty", rename = "chimicalElementSelected")]
    chimical_element_selected: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct TimeRangeSelection {
    #[serde(rename = "startTime")]
    start_time: Option<String>,
    #[serde(rename = "endTime")]
    end_time: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PignatSelectedMetric {
    name: String,
    #[serde(rename = "timeRange")]
    time_range: Option<TimeRangeSelection>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SelectedMetricsBySensor {
    chromeleon_offline: Vec<String>,
    chromeleon_online: Vec<MetricSelected>,
    chromeleon_online_permanent_gas: Vec<MetricSelected>,
    pignat: Vec<PignatSelectedMetric>,
    resume: Vec<String>,
}

fn resolve_embedded_python(app: &AppHandle) -> Option<PathBuf> {
    let resource_dir = app.path().resource_dir().ok()?;
    let base = resource_dir.join("python-runtime").join("venv");
    
    #[cfg(target_os = "windows")]
    {
        // Essayer d'abord le Python portable (racine)
        let portable_bin = base.join("python.exe");
        if portable_bin.exists() {
            return Some(portable_bin);
        }
        // Fallback vers le venv classique
        let venv_bin = base.join("Scripts").join("python.exe");
        if venv_bin.exists() {
            return Some(venv_bin);
        }
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        // Essayer d'abord le Python portable (racine)
        let portable_bin = base.join("python3");
        if portable_bin.exists() {
            return Some(portable_bin);
        }
        // Fallback vers le venv classique
        let venv_bin = base.join("bin").join("python3");
        if venv_bin.exists() {
            return Some(venv_bin);
        }
    }
    
    None
}

fn resolve_python_main(app: &AppHandle) -> Result<PathBuf, String> {
    let resource_dir = app.path().resource_dir()
        .map_err(|e| format!("Cannot get resource directory: {}", e))?;
    let main_py = resource_dir.join("python-scripts").join("main.py");
    if main_py.exists() {
        Ok(main_py)
    } else {
        Err("main.py introuvable dans les resources".into())
    }
}

fn run_python(app: &AppHandle, args: &[&str]) -> Result<CommandOutput, String> {
    let script = resolve_python_main(app)?;
    let python_bin = resolve_embedded_python(app)
        .unwrap_or_else(|| PathBuf::from("python3"));

    let output = std::process::Command::new(&python_bin)
        .arg("-u")
        .arg(&script)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to execute Python ({:?}): {}", python_bin, e))?;

    let stdout = String::from_utf8(output.stdout)
        .map_err(|e| format!("Invalid UTF-8 in stdout: {}", e))?;
    let stderr = String::from_utf8(output.stderr)
        .map_err(|e| format!("Invalid UTF-8 in stderr: {}", e))?;

    if !output.status.success() {
        return Err(if stderr.trim().is_empty() {
            format!("Python exited with error (code {:?})", output.status.code())
        } else {
            stderr
        });
    }
    if stdout.trim().is_empty() && !stderr.trim().is_empty() {
        return Err(stderr);
    }
    if !stderr.trim().is_empty() {
        eprintln!("Python debug: {}", stderr);  // Affiche les logs de debug
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
fn context_is_correct(app: tauri::AppHandle, dir_path: String) -> Result<bool, String> {
    let out = run_python(&app, &["CONTEXT_IS_CORRECT", &dir_path])?;
    let json = parse_python_json(&out.stdout)?;
    json.as_bool()
        .ok_or_else(|| "Invalid JSON: expected boolean".into())
}

#[tauri::command]
fn get_context_masses(app: tauri::AppHandle, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python(&app, &["GET_CONTEXT_MASSES", &dir_path])?;
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
fn get_context_b64(app: tauri::AppHandle, dir_path: String) -> Result<String, String> {
    let out = run_python(&app, &["GET_CONTEXT_B64", &dir_path])?;
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
fn get_context_experience_name(app: tauri::AppHandle, dir_path: String) -> Result<String, String> {
    let out = run_python(&app, &["GET_CONTEXT_EXPERIENCE_NAME", &dir_path])?;
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
fn get_graphs_available(app: tauri::AppHandle, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python(&app, &["GET_GRAPHS_AVAILABLE", &dir_path])?;
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
fn get_time_range(app: tauri::AppHandle, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python(&app, &["GET_TIME_RANGE", &dir_path])?;
    if out.stdout.trim().is_empty() {
        return Err(if out.stderr.trim().is_empty() {
            "Empty stdout from Python".into()
        } else {
            out.stderr
        });
    }
    parse_python_json(&out.stdout)
}

#[tauri::command(rename_all = "camelCase")]
async fn generate_and_save_excel(
    app: tauri::AppHandle,
    dir_path: String,
    metric_wanted: SelectedMetricsBySensor,
    destination_path: String,
) -> Result<serde_json::Value, String> {
    // Debug: Afficher les métriques reçues
    println!("Received metrics: {:?}", metric_wanted);
    
    // Sérialiser l'objet reçu en JSON pour Python
    let metrics_json = serde_json::to_string(&metric_wanted)
        .map_err(|e| format!("Failed to serialize metrics: {e}"))?;
    
    println!("Serialized JSON: {}", metrics_json);

    let dest = std::path::PathBuf::from(&destination_path);
    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Cannot create output directory {}: {e}", parent.display()))?;
    }

    let out = run_python(&app, &[
        "GENERATE_EXCEL_TO_FILE",
        &metrics_json,
        &dir_path,
        &destination_path,
    ])?;

    parse_python_json(&out.stdout)
}

/// ---------- Utilitaires fichier / système ----------

#[command]
fn get_documents_dir() -> Result<String, String> {
    document_dir()
        .ok_or_else(|| "Impossible de récupérer le dossier Documents".into())
        .map(|p| p.to_string_lossy().into_owned())
}

#[command]
async fn remove_dir(dir_path: String) -> Result<(), String> {
    if tokio::fs::try_exists(&dir_path).await
        .map_err(|e| format!("Erreur vérification existence répertoire : {}", e))? {
        tokio::fs::remove_dir_all(&dir_path).await
            .map_err(|e| format!("Erreur suppression répertoire : {}", e))?;
    }
    Ok(())
}

#[command]
async fn write_file(destination_path: String, contents: Vec<u8>) -> Result<(), String> {
    if let Some(parent) = Path::new(&destination_path).parent() {
        tokio::fs::create_dir_all(parent).await
            .map_err(|e| format!("Erreur création répertoire : {}", e))?;
    }
    tokio::fs::write(&destination_path, contents).await
        .map_err(|e| format!("Erreur lors de l'écriture : {}", e))?;
    println!("✅ Écriture de `{}` réussie", destination_path);
    Ok(())
}

#[command]
async fn copy_file(source_path: String, destination_path: String) -> Result<(), String> {
    if let Some(parent) = Path::new(&destination_path).parent() {
        tokio::fs::create_dir_all(parent).await
            .map_err(|e| format!("Erreur création répertoire : {}", e))?;
    }
    tokio::fs::copy(&source_path, &destination_path).await
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
            get_context_experience_name,
            get_graphs_available,
            get_time_range,
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