use std::{fs, path::Path};
use tauri::command;
use dirs::document_dir;
use std::process::Command;
use serde::{Serialize, Deserialize};

#[derive(Serialize)]
struct CommandOutput {
    stdout: String,
    stderr: String,
}

#[derive(Serialize, Deserialize)]
struct SelectedMetricsBySensor {
    chromeleon_offline: Vec<String>,
    chromeleon_online: Vec<String>,
    pigna: Vec<String>,
}

// Constante pour le chemin du script Python
const SCRIPT_PATH: &str = "/home/lucaslhm/Documents/ETIC/Bobine/project/desktop_app/src-tauri/python-scripts/main.py";

#[tauri::command]
fn run_python_script_with_dir(dir_path: String, action: String) -> Result<CommandOutput, String> {
    let output = Command::new("python3")
        .arg(SCRIPT_PATH)
        .arg(action)
        .arg(dir_path)
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e))?;

    let stdout = String::from_utf8(output.stdout).map_err(|e| format!("Invalid UTF-8 in stdout: {}", e))?;
    let stderr = String::from_utf8(output.stderr).map_err(|e| format!("Invalid UTF-8 in stderr: {}", e))?;

    Ok(CommandOutput { stdout, stderr })
}

#[tauri::command]
fn generate_excel_file(dir_path: String, metric_wanted: SelectedMetricsBySensor) -> Result<String, String> {
    let metrics_json = serde_json::to_string(&metric_wanted)
        .map_err(|e| format!("Failed to serialize metrics: {}", e))?;

    println!("Executing Python script with:");
    println!("  Script: {}", SCRIPT_PATH);
    println!("  Action: GENERATE_EXCEL");
    println!("  Metrics: {}", metrics_json);
    println!("  Directory: {}", dir_path);

    let output = Command::new("python3")
        .arg(SCRIPT_PATH)
        .arg("GENERATE_EXCEL")
        .arg(&metrics_json)
        .arg(&dir_path)
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    println!("Python script output:");
    println!("  STDOUT: {}", stdout);
    println!("  STDERR: {}", stderr);
    println!("  Status: {}", output.status);

    if !output.status.success() {
        return Err(format!("Command failed with status: {} - STDOUT: {} - STDERR: {}", 
                          output.status, stdout, stderr));
    }

    Ok(stdout.trim().to_string())
}
/// Renvoie le chemin absolu du dossier Documents de l'utilisateur.
#[command]
fn get_documents_dir() -> Result<String, String> {
    document_dir()
        .ok_or_else(|| "Impossible de récupérer le dossier Documents".into())
        .map(|p| p.to_string_lossy().into_owned())
}

#[command]
fn remove_dir(dir_path: String) -> Result<(), String> {
    if Path::new(&dir_path).exists() {
        fs::remove_dir_all(&dir_path).map_err(|e| format!("Erreur suppression répertoire : {}", e))?;
    }
    Ok(())
}

#[command]
fn my_custom_command(invoke_message: String) {
    println!("I was invoked from JavaScript, with this message: {}", invoke_message);
}

/// Écrit des données binaires dans un fichier à partir d'un Vec<u8>
#[command]
fn write_file(destination_path: String, contents: Vec<u8>) -> Result<(), String> {
    // Créer les répertoires parents si nécessaire
    if let Some(parent) = Path::new(&destination_path).parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Erreur création répertoire : {}", e))?;
    }

    // Écrire le fichier
    fs::write(&destination_path, contents)
        .map_err(|e| format!("Erreur lors de l'écriture : {}", e))?;

    println!("✅ Écriture de `{}` réussie", destination_path);
    Ok(())
}

/// Copie le fichier source vers la destination
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

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            run_python_script_with_dir,
            generate_excel_file,
            get_documents_dir,
            write_file,
            copy_file,
            my_custom_command,
            remove_dir 
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}