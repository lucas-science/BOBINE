 const copyFiles = async () => {
    if (files.length === 0) {
      addLog("❌ Aucun fichier à copier", "error");
      return;
    }
    const test = await invoke('my_custom_command', { invokeMessage: 'Hello!' });
    addLog(`🔧 Commande Rust exécutée: ${test}`, "info");
    addLog(`🚀 Copie de ${files.length} fichier(s)…`, "info");

    try {
      // 1) Récupérer le dossier Documents
      const docsDir: string = await invoke("get_documents_dir");
      addLog(`📂 Documents: ${docsDir}`, "info");

      for (const file of files) {
        const destName = `bobine_${Date.now()}_${file.name}`;
        // Correction: utiliser le bon séparateur de chemin
        const destPath = `${docsDir}${docsDir.endsWith('/') || docsDir.endsWith('\\') ? '' : '/'}${destName}`;

        addLog(`📋 Copie de ${file.name} → ${destName}…`, "info");

        // 2) Lire le contenu du fichier
        const buffer = await file.arrayBuffer();
        const uint8 = new Uint8Array(buffer);
        // Convertir en liste de nombres pour sérialiser dans invoke
        const arr = Array.from(uint8);

        // 3) Envoyer à Rust pour écriture
        await invoke("write_file", {
          destinationPath: destPath,  // camelCase côté JS
          contents: arr,
        });
        
        addLog(`✅ ${file.name} copié sous ${destName}`, "success");
      }

      addLog("🎉 Copie terminée !", "success");
      
      // Optionnel: vider la liste des fichiers après copie réussie
      setFiles([]);
      
    } catch (error) {
      addLog(`❌ Erreur lors de la copie: ${error}`, "error");
    }
  };