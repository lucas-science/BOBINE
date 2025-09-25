use tauri::{command, AppHandle, Manager, State};
use dirs::document_dir;
use serde::{Serialize, Deserialize};
use serde_json::Value as JsonValue;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::io::{BufRead, BufReader, Write};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

#[derive(Serialize)]
pub struct CommandOutput {
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

struct PythonProcess {
    child: Child,
    stdin: std::process::ChildStdin,
    stdout: BufReader<std::process::ChildStdout>,
    last_used: Instant,
}

impl PythonProcess {
    fn new(python_bin: &PathBuf, app: &AppHandle) -> Result<Self, String> {
        let mut cmd = if python_bin.file_name()
            .and_then(|name| name.to_str())
            .map(|name| name.starts_with("data_processor"))
            .unwrap_or(false)
        {
            // Executable compilé - mode interactif
            let mut cmd = Command::new(python_bin);
            cmd.arg("--interactive"); // On va modifier le Python pour supporter ce mode
            cmd
        } else {
            // Script Python traditionnel
            let script = app.path().resource_dir()
                .map_err(|e| format!("Cannot get resource directory: {}", e))?
                .join("python-scripts").join("main.py");
            let mut cmd = Command::new(python_bin);
            cmd.arg("-u").arg(&script).arg("--interactive");
            cmd
        };

        // Configuration spécifique pour Windows pour masquer le terminal
        #[cfg(target_os = "windows")]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x08000000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }

        let mut child = cmd
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn Python process: {}", e))?;

        let stdin = child.stdin.take()
            .ok_or_else(|| "Failed to get stdin handle".to_string())?;
        let stdout = child.stdout.take()
            .ok_or_else(|| "Failed to get stdout handle".to_string())?;

        Ok(PythonProcess {
            child,
            stdin,
            stdout: BufReader::new(stdout),
            last_used: Instant::now(),
        })
    }

    fn send_command(&mut self, args: &[&str]) -> Result<CommandOutput, String> {
        self.last_used = Instant::now();
        
        // Envoyer la commande au processus Python
        let command = args.join("\t");
        writeln!(self.stdin, "{}", command)
            .map_err(|e| format!("Failed to write to Python stdin: {}", e))?;
        self.stdin.flush()
            .map_err(|e| format!("Failed to flush Python stdin: {}", e))?;

        // Lire la réponse
        let mut response = String::new();
        let stderr = String::new();
        
        // Lire ligne par ligne jusqu'à voir notre marqueur de fin
        loop {
            let mut line = String::new();
            match self.stdout.read_line(&mut line) {
                Ok(0) => return Err("Python process ended unexpectedly".to_string()),
                Ok(_) => {
                    if line.trim() == "<<<END_RESPONSE>>>" {
                        break;
                    }
                    response.push_str(&line);
                }
                Err(e) => return Err(format!("Failed to read from Python stdout: {}", e)),
            }
        }

        Ok(CommandOutput {
            stdout: response.trim().to_string(),
            stderr,
        })
    }

    fn is_healthy(&mut self) -> bool {
        match self.child.try_wait() {
            Ok(Some(_)) => false, // Process has exited
            Ok(None) => true,     // Process is still running
            Err(_) => false,      // Error checking process status
        }
    }

    fn should_restart(&self) -> bool {
        // Redémarrer après 10 minutes d'inactivité pour éviter les fuites mémoire
        self.last_used.elapsed() > Duration::from_secs(600)
    }
}

pub struct PythonService {
    process: Arc<Mutex<Option<PythonProcess>>>,
    python_bin: PathBuf,
    app_handle: AppHandle,
}

impl PythonService {
    pub fn new(python_bin: PathBuf, app_handle: AppHandle) -> Self {
        Self {
            process: Arc::new(Mutex::new(None)),
            python_bin,
            app_handle,
        }
    }

    pub fn execute(&self, args: &[&str]) -> Result<CommandOutput, String> {
        let mut process_guard = self.process.lock()
            .map_err(|e| format!("Failed to lock Python service: {}", e))?;

        // Vérifier si on a besoin de créer/recréer le processus
        let need_new_process = match process_guard.as_mut() {
            None => true,
            Some(process) => !process.is_healthy() || process.should_restart(),
        };

        if need_new_process {
            // Nettoyer l'ancien processus si nécessaire
            if let Some(mut old_process) = process_guard.take() {
                let _ = old_process.child.kill();
                let _ = old_process.child.wait();
            }

            // Créer un nouveau processus
            let new_process = PythonProcess::new(&self.python_bin, &self.app_handle)?;
            *process_guard = Some(new_process);
        }

        // Exécuter la commande
        process_guard.as_mut()
            .unwrap()
            .send_command(args)
    }
}

pub type PythonServiceState = Arc<PythonService>;

fn resolve_embedded_python(app: &AppHandle) -> Option<PathBuf> {
    let resource_dir = app.path().resource_dir().ok()?;
    let runtime_dir = resource_dir.join("python-runtime");
    
    #[cfg(target_os = "windows")]
    {
        // Utiliser l'executable compilé avec PyInstaller
        let compiled_exe = runtime_dir.join("data_processor.exe");
        if compiled_exe.exists() {
            return Some(compiled_exe);
        }
        // Fallback vers python3 système pour Windows
        let system_python = PathBuf::from("python");
        return Some(system_python);
    }
    
    #[cfg(target_os = "linux")]
    {
        // Pour Linux, utiliser le venv intégré comme précédemment
        let venv_bin = runtime_dir.join("venv").join("bin").join("python3");
        if venv_bin.exists() {
            return Some(venv_bin);
        }
        // Fallback vers python3 système
        let system_python = PathBuf::from("python3");
        return Some(system_python);
    }
    
    #[cfg(target_os = "macos")]
    {
        // Pour macOS, utiliser le venv intégré
        let venv_bin = runtime_dir.join("venv").join("bin").join("python3");
        if venv_bin.exists() {
            return Some(venv_bin);
        }
        // Fallback vers python3 système
        let system_python = PathBuf::from("python3");
        return Some(system_python);
    }
    
    // Fallback ultime pour les plateformes non supportées
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
    // Fallback pour compatibilité - utilise l'ancien système si le service persistant échoue
    let python_bin = resolve_embedded_python(app)
        .unwrap_or_else(|| PathBuf::from("python3"));

    // Vérifier si on utilise l'executable compilé ou le script Python
    let output = if python_bin.file_name()
        .and_then(|name| name.to_str())
        .map(|name| name.starts_with("data_processor"))
        .unwrap_or(false)
    {
        // Utiliser l'executable compilé directement
        std::process::Command::new(&python_bin)
            .args(args)
            .output()
            .map_err(|e| format!("Failed to execute compiled Python ({:?}): {}", python_bin, e))?
    } else {
        // Fallback vers le script Python traditionnel pour les autres plateformes
        let script = resolve_python_main(app)?;
        std::process::Command::new(&python_bin)
            .arg("-u")
            .arg(&script)
            .args(args)
            .output()
            .map_err(|e| format!("Failed to execute Python ({:?}): {}", python_bin, e))?
    };

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

fn run_python_with_service(python_service: &PythonService, args: &[&str]) -> Result<CommandOutput, String> {
    // Tenter d'utiliser le service persistant
    match python_service.execute(args) {
        Ok(output) => Ok(output),
        Err(e) => {
            eprintln!("Python service failed, falling back to direct execution: {}", e);
            // Fallback vers l'exécution directe si le service échoue
            run_python(&python_service.app_handle, args)
        }
    }
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
fn context_is_correct(python_service: State<PythonServiceState>, dir_path: String) -> Result<bool, String> {
    let out = run_python_with_service(&python_service, &["CONTEXT_IS_CORRECT", &dir_path])?;
    let json = parse_python_json(&out.stdout)?;
    json.as_bool()
        .ok_or_else(|| "Invalid JSON: expected boolean".into())
}

#[tauri::command]
fn validate_context(python_service: State<PythonServiceState>, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python_with_service(&python_service, &["VALIDATE_CONTEXT", &dir_path])?;
    let json = parse_python_json(&out.stdout)?;
    json.as_object()
        .map(|obj| serde_json::to_value(obj).unwrap())
        .ok_or_else(|| "Invalid JSON: expected object".into())
}

#[tauri::command]
fn get_context_masses(python_service: State<PythonServiceState>, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python_with_service(&python_service, &["GET_CONTEXT_MASSES", &dir_path])?;
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
fn get_context_b64(python_service: State<PythonServiceState>, dir_path: String) -> Result<String, String> {
    let out = run_python_with_service(&python_service, &["GET_CONTEXT_B64", &dir_path])?;
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
fn get_context_experience_name(python_service: State<PythonServiceState>, dir_path: String) -> Result<String, String> {
    let out = run_python_with_service(&python_service, &["GET_CONTEXT_EXPERIENCE_NAME", &dir_path])?;
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
fn get_graphs_available(python_service: State<PythonServiceState>, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python_with_service(&python_service, &["GET_GRAPHS_AVAILABLE", &dir_path])?;
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
fn get_time_range(python_service: State<PythonServiceState>, dir_path: String) -> Result<JsonValue, String> {
    let out = run_python_with_service(&python_service, &["GET_TIME_RANGE", &dir_path])?;
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
    python_service: State<'_, PythonServiceState>,
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

    let out = run_python_with_service(&python_service, &[
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
        .setup(|app| {
            // Initialiser le service Python persistant au démarrage
            let python_bin = resolve_embedded_python(&app.handle())
                .unwrap_or_else(|| PathBuf::from("python3"));
            let python_service = Arc::new(PythonService::new(python_bin, app.handle().clone()));
            
            // Pré-lancer le processus Python pour réduire la latence
            let service_clone = python_service.clone();
            std::thread::spawn(move || {
                // Démarrer le processus Python en arrière-plan
                match service_clone.execute(&["CONTEXT_IS_CORRECT", "/tmp"]) {
                    Ok(_) => println!("✅ Service Python pré-lancé avec succès"),
                    Err(e) => println!("⚠️  Échec du pré-lancement Python (normal si pas de données): {}", e),
                }
            });
            
            app.manage(python_service);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Python actions exposées une par une :
            context_is_correct,
            validate_context,
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