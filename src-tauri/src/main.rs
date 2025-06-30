// src-tauri/src/main.rs

// Empêche la console supplémentaire sous Windows (release).
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod lib;

fn main() {
  // On délègue tout à notre fonction `run()` dans lib.rs
  lib::run();
}
