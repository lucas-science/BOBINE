# Implémentation du Drag & Drop pour Tauri

## 🎯 Objectif

Permettre aux utilisateurs de glisser-déposer des fichiers depuis l'explorateur Windows directement dans les zones d'upload de l'application Tauri.

## 🏗️ Architecture

### 1. **FileDropContext** (`src/contexts/FileDropContext.tsx`)

Le contexte global qui gère tous les événements Tauri de drag and drop.

**Responsabilités :**
- Écoute les événements Tauri globaux : `tauri://file-drop`, `tauri://file-drop-hover`, `tauri://file-drop-cancelled`
- Maintient une Map des zones enregistrées (zoneId → callback)
- Gère la zone active (celle qui recevra les fichiers lors du drop)
- Route les fichiers vers la bonne zone quand le drop se produit

**Fonctionnement :**
```
1. Zone A survolée → setActiveZone("zone-a")
2. Fichiers déposés → Tauri émet "tauri://file-drop"
3. Contexte convertit les chemins en File objects
4. Contexte appelle la callback de la zone active
```

### 2. **FileUploadZone** (`src/components/upload/FileUploadZone.tsx`)

Chaque zone d'upload s'enregistre auprès du contexte et gère son propre état visuel.

**Responsabilités :**
- S'enregistre avec un ID unique au montage
- Détecte le survol avec les événements HTML drag (`onDragEnter`, `onDragLeave`, `onDragOver`)
- Marque la zone comme active quand elle est survolée
- Fournit un feedback visuel (animation, changement de couleur, texte dynamique)
- Reçoit les fichiers via la callback enregistrée

**Événements clés :**

| Événement | Action |
|-----------|--------|
| `onDragEnter` | Incrémente un compteur, marque comme active si compteur = 1 |
| `onDragLeave` | Décrémente le compteur, désactive si compteur = 0 |
| `onDragOver` | Empêche le comportement par défaut du navigateur |
| `onDrop` | Réinitialise l'état (Tauri gère les fichiers séparément) |

**Note importante :** Le compteur de drag (`dragCounterRef`) est nécessaire car `onDragEnter` et `onDragLeave` se déclenchent aussi sur les éléments enfants. Sans compteur, l'animation scintillerait.

### 3. **fileUtils.ts** (`src/lib/fileUtils.ts`)

Utilitaire pour convertir les chemins de fichiers Windows en objets File JavaScript.

**Fonction principale :** `pathsToFiles(paths: string[])`

```typescript
// Tauri donne des chemins comme : "C:\\Users\\..\\file.xlsx"
// On les convertit en objets File pour compatibilité avec le reste de l'app
const files = await pathsToFiles(filePaths);
```

**Étapes :**
1. Lit le contenu binaire avec `@tauri-apps/plugin-fs`
2. Détecte le MIME type basé sur l'extension
3. Crée un Blob puis un File object

## 🎨 Animations & Feedback Visuel

Quand une zone est survolée pendant un drag :

| Élément | État Normal | État Survol (Drag) |
|---------|-------------|-------------------|
| **Bordure** | `border-2 border-dashed border-border` | `border-4 border-primary ring-4 ring-primary/20` |
| **Fond** | `bg-background` | `bg-primary/15` |
| **Échelle** | `scale-100` | `scale-[1.03]` |
| **Ombre** | Aucune | `shadow-xl` |
| **Icône Upload** | Gris statique | Bleu avec `animate-bounce` |
| **Texte** | "Glissez-déposez..." | "Déposez les fichiers ici !" |
| **Titre** | Taille normale | Agrandi avec couleur primaire |

## 🔄 Flux complet du Drag & Drop

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Utilisateur commence à drag des fichiers depuis Windows │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Tauri émet "tauri://file-drop-hover" (survol fenêtre)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. HTML onDragEnter sur zone A                             │
│    → dragCounter++                                          │
│    → setIsDragOver(true)                                    │
│    → setActiveZone("zone-a")                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Zone A affiche animation (bordure bleue, scale, etc.)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Utilisateur dépose les fichiers                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Tauri émet "tauri://file-drop" avec chemins             │
│    Payload: ["C:\\Users\\...\\file1.xlsx", ...]            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. FileDropContext convertit chemins → File objects        │
│    await pathsToFiles(event.payload)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Contexte appelle callback de zone A                     │
│    zonesRef.current.get("zone-a")(files)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Zone A reçoit les fichiers et les ajoute à sa liste     │
│    → onFileSelect([...selectedFiles, ...files])             │
│    → setIsDragOver(false)                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Comment tester

### En mode développement (Tauri)

```bash
npm run tauri-dev
```

1. L'application Tauri se lance
2. Allez sur la page d'upload (/)
3. Ouvrez l'explorateur Windows
4. Glissez des fichiers Excel/CSV vers une zone d'upload
5. **Observer :**
   - ✅ La zone change de couleur (bleu) pendant le survol
   - ✅ L'icône Upload devient bleue et bounce
   - ✅ Le texte change : "Déposez les fichiers ici !"
   - ✅ La zone grossit légèrement (scale)
   - ✅ Après le drop, les fichiers apparaissent dans la liste

6. **Ouvrir la console DevTools (F12) :**
   - `[FileDropContext] Setting up Tauri listeners`
   - `[FileDropContext] Registering zone: :r1:` (x6 zones)
   - `[FileUploadZone Context files] Drag enter, counter: 1`
   - `[FileUploadZone Context files] Set as active zone`
   - `[FileDropContext] File drop event received`
   - `[FileDropContext] Routing 2 files to zone: :r1:`

### En mode développement (Navigateur)

```bash
npm run dev
```

- Le drag and drop fonctionne aussi grâce au fallback HTML5
- Les fichiers sont accessibles via `e.dataTransfer.files` directement
- Pas de conversion de chemins nécessaire

## 🐛 Débogage

### Le drag and drop ne fonctionne pas

**Vérifications :**

1. **Vérifier les logs de la console :**
   ```
   [FileDropContext] Setting up Tauri listeners
   [FileDropContext] Registering zone: ...
   ```
   Si absent → Le FileDropProvider n'est pas monté

2. **Vérifier que les zones s'enregistrent :**
   ```
   [FileDropContext] Registering zone: :r1:
   ```
   Devrait apparaître 6 fois (context, pignat, chromeleon x3, resume)

3. **Vérifier le survol :**
   ```
   [FileUploadZone XXX] Drag enter, counter: 1
   [FileUploadZone XXX] Set as active zone
   ```
   Si absent → Les événements HTML drag ne se déclenchent pas

4. **Vérifier le drop Tauri :**
   ```
   [FileDropContext] File drop event received
   ```
   Si absent → Tauri n'émet pas l'événement (vérifier tauri.conf.json)

### L'animation ne s'affiche pas

- Vérifier que `isDragOver` passe à `true` dans les logs
- Vérifier que Tailwind compile les classes (`border-primary`, `animate-bounce`)
- Vérifier qu'il n'y a pas de CSS conflictuel

### Les fichiers vont dans la mauvaise zone

- Vérifier quelle zone est active dans les logs :
  ```
  [FileDropContext] Routing X files to zone: :rY:
  ```
- Comparer avec la zone survolée visuellement

### Erreur "Can't read file"

- Vérifier les permissions du plugin fs de Tauri
- Vérifier que le chemin est valide (Windows : `C:\\...`)
- Vérifier les logs :
  ```
  [FileDropContext] Error processing dropped files: ...
  ```

## 📝 Notes importantes

1. **Multi-zones :** Le système supporte plusieurs zones simultanées. Seule la zone survolée reçoit les fichiers.

2. **Compatibilité :** Fonctionne en mode navigateur (HTML5) ET en mode Tauri (événements natifs).

3. **Performance :** La conversion de chemins → File objects est asynchrone et gère les gros fichiers.

4. **Sécurité :** Tauri ne donne accès qu'aux fichiers explicitement droppés par l'utilisateur.

5. **Drag counter :** Nécessaire car `onDragEnter`/`onDragLeave` se déclenchent aussi sur les enfants HTML. Sans compteur, l'animation scintillerait.

## 🔧 Configuration Tauri

Dans `src-tauri/tauri.conf.json`, le file drop est activé par défaut dans Tauri v2. Aucune configuration supplémentaire requise.

Les événements émis automatiquement :
- `tauri://file-drop` : Fichiers déposés (payload = array de chemins)
- `tauri://file-drop-hover` : Fichiers survolent la fenêtre
- `tauri://file-drop-cancelled` : Drag annulé (fichiers sortis de la fenêtre)

## 📦 Dépendances

```json
{
  "@tauri-apps/api": "^2.0.1",
  "@tauri-apps/plugin-fs": "^2.4.0"
}
```

## 🎉 Fonctionnalités implémentées

- ✅ Drag & drop depuis l'explorateur Windows
- ✅ Détection automatique de la zone survolée
- ✅ Feedback visuel avec animations fluides
- ✅ Support multi-zones avec routing intelligent
- ✅ Gestion des limites de fichiers par zone
- ✅ Messages d'erreur en français
- ✅ Compatibilité mode dev (navigateur) et production (Tauri)
- ✅ Logs détaillés pour le débogage
- ✅ Badge "Limite atteinte" conditionnel
- ✅ Conversion automatique des chemins en File objects
