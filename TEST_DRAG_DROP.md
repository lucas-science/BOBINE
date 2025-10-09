# Guide de Test - Drag & Drop

## 🚀 Lancer l'application

```bash
npm run tauri-dev
```

## ✅ Checklist de test

### 1. Vérifier que l'application démarre
- [ ] L'application Tauri s'ouvre
- [ ] La page d'upload s'affiche avec les 5 zones (Context, Pignat, Chromeleon x3)

### 2. Ouvrir la console pour voir les logs
- [ ] Appuyer sur `F12` pour ouvrir DevTools
- [ ] Aller dans l'onglet "Console"
- [ ] Vérifier que vous voyez les logs de setup :
  ```
  [FileDropContext] Registering zone: :rX:
  [FileUploadZone XXX] Tauri listeners setup complete
  ```

### 3. Tester l'animation drag (sans fichier)
- [ ] Survoler une zone avec la souris
- [ ] Vérifier le hover effect (bordure change légèrement)

### 4. Tester le drag and drop
- [ ] Ouvrir l'explorateur Windows
- [ ] Sélectionner 1 ou 2 fichiers (Excel, CSV, txt...)
- [ ] **Commencer à les glisser** vers l'application

**OBSERVER DANS LA CONSOLE :**
- [ ] Log : `[FileUploadZone XXX] Tauri listeners setup complete`
- [ ] Quand vous entrez dans une zone : `[FileUploadZone XXX] Drag enter, counter: 1`
- [ ] Quand vous entrez dans une zone : `[FileUploadZone XXX] Set as active zone`

**OBSERVER VISUELLEMENT :**
- [ ] La zone change de couleur (bordure bleue, fond bleu clair)
- [ ] La zone grossit légèrement
- [ ] L'icône Upload devient bleue et bounce
- [ ] Le texte change : "Déposez les fichiers ici !"

### 5. Relâcher les fichiers
- [ ] Déposer les fichiers dans la zone active

**OBSERVER DANS LA CONSOLE :**
- [ ] `[FileUploadZone XXX] File drop event:` avec le type "drop"
- [ ] `[FileUploadZone XXX] Drop detected, active zone: :rX:`
- [ ] `[FileUploadZone XXX] Converting paths:` avec les chemins Windows
- [ ] `[FileUploadZone XXX] Converted X files`
- [ ] `[FileUploadZone XXX] handleNewFiles called with X files`

**OBSERVER VISUELLEMENT :**
- [ ] Les fichiers apparaissent dans la liste en dessous
- [ ] Chaque fichier a son nom et sa taille
- [ ] Le compteur se met à jour : "1/5 fichier(s)"

### 6. Tester plusieurs fichiers
- [ ] Glisser 2-3 fichiers d'un coup
- [ ] Vérifier qu'ils apparaissent tous

### 7. Tester la limite
- [ ] Glisser plus de fichiers que la limite (ex: 10 fichiers dans une zone qui n'en accepte que 5)
- [ ] Vérifier le message d'erreur : "Limite dépassée ! Maximum X fichier(s) par zone."

### 8. Tester le clic pour parcourir
- [ ] Cliquer sur une zone (pas glisser)
- [ ] Vérifier que l'explorateur de fichiers Windows s'ouvre
- [ ] Sélectionner des fichiers
- [ ] Vérifier qu'ils s'ajoutent

## 🐛 Si ça ne fonctionne pas

### Problème : Aucun log dans la console
**Solution :**
- Vérifier que vous êtes bien en mode Tauri (`npm run tauri-dev` et pas `npm run dev`)
- Redémarrer l'application

### Problème : Pas d'animation quand je glisse
**Vérifier dans la console :**
- Chercher `[FileUploadZone XXX] Drag enter`
  - **Si absent :** Les événements HTML ne se déclenchent pas
  - **Si présent :** L'animation devrait s'afficher (vérifier le CSS)

### Problème : Animation OK mais pas de fichiers après drop
**Vérifier dans la console :**
- Chercher `[FileUploadZone XXX] File drop event:`
  - **Si absent :** Tauri n'émet pas l'événement
    - → Vérifier `src-tauri/capabilities/default.json` (permissions)
    - → Redémarrer l'application
  - **Si présent :** Vérifier les logs suivants pour voir où ça bloque

### Problème : "Error converting files"
**Vérifier dans la console :**
- Chercher le détail de l'erreur
- Vérifier les permissions du plugin fs de Tauri
- Vérifier que le chemin du fichier est valide

### Problème : Les fichiers vont dans la mauvaise zone
**Vérifier dans la console :**
- Chercher `Drop detected, active zone: :rX:`
- Comparer avec `Set as active zone` pour voir quelle zone était survolée

## 📊 Logs attendus (exemple complet)

```
[FileDropContext] Registering zone: :r1:
[FileDropContext] Registering zone: :r2:
[FileDropContext] Registering zone: :r3:
[FileDropContext] Registering zone: :r4:
[FileDropContext] Registering zone: :r5:
[FileUploadZone Context files] Tauri listeners setup complete
[FileUploadZone Pignat data] Tauri listeners setup complete
[FileUploadZone GC-Online data] Tauri listeners setup complete
[FileUploadZone GC-Offline data] Tauri listeners setup complete
[FileUploadZone GC-Online Permanent Gas data] Tauri listeners setup complete

// Utilisateur glisse des fichiers vers "Context files"
[FileUploadZone Context files] Drag enter, counter: 1
[FileUploadZone Context files] Set as active zone

// Utilisateur relâche
[FileUploadZone Context files] File drop event: {type: "drop", paths: ["C:\\Users\\...\\file.xlsx"]}
[FileUploadZone Context files] Drop detected, active zone: :r1:
[FileUploadZone Context files] Converting paths: ["C:\\Users\\...\\file.xlsx"]
[FileUploadZone Context files] Converted 1 files
[FileUploadZone Context files] handleNewFiles called with 1 files
```

## 🎯 Comportements attendus

| Action | Résultat visuel | Logs console |
|--------|-----------------|--------------|
| Hover zone (souris) | Bordure change légèrement | Aucun |
| Drag enter zone | Bordure bleue + icon bounce + texte change + scale | `Drag enter, counter: 1` + `Set as active zone` |
| Drag leave zone | Retour à la normale | `Drag leave, counter: 0` + `Unset active zone` |
| Drop fichiers | Fichiers ajoutés à la liste | `File drop event` + `Converting paths` + `Converted X files` |
| Drop trop de fichiers | Message erreur rouge | `Limite dépassée !` |
| Clic zone | Explorateur s'ouvre | Aucun |

## 🔧 Commandes utiles

```bash
# Lancer en mode dev
npm run tauri-dev

# Nettoyer le build
npm run tauri-clean

# Rebuild complet
npm run tauri-clean && npm run tauri-dev
```

## 📝 Notes

- Les événements `onDragEnter` / `onDragLeave` peuvent se déclencher plusieurs fois (éléments enfants). C'est normal, on utilise un compteur pour gérer ça.
- Dans Tauri, `e.dataTransfer.files` est vide. Les fichiers arrivent via `onFileDropEvent`.
- En mode navigateur (`npm run dev`), le drag & drop HTML5 classique fonctionne.
