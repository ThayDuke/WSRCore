================================================================================
             DEC - DUKE ENGLISH CENTER SYSTEM ARCHITECTURE & README
================================================================================

1. OVERVIEW & VISION
--------------------
Duke English Center System (DEC) is an offline-first, locally-hosted learning 
management and interactive educational platform designed for English tutoring centers. 
The system automates the rendering of customized HTML5 lessons, manages classroom 
slides, facilitates multiple-choice and listening exercises, serves gamified tasks, 
and administers adaptive examinations with dynamic grading.

Key Capabilities:
- Local Server Architecture: Works entirely offline using a lightweight Flask server.
- High-Fidelity Text-to-Speech (TTS): Uses Microsoft Edge TTS integration for pronunciation.
- Adaptive Assessment Engine: Dynamically shifts question difficulty based on accuracy.
- Master UI Consistency: Standardized design themes across all tools to eliminate interface drift.
- Developer Workflows: Integrated tools to safeguard file system states and audit updates.


2. TECH STACK & SYSTEM ARCHITECTURE
-----------------------------------
- Backend:
  - Python 3.x (Flask core for HTTP endpoints and APIs).
  - edge-tts (High-quality voice generation via Edge Speech APIs).
  - pystray & Pillow (Local system tray application management).
  - ctypes & Win32 API (For window control, background execution, and console hiding).
- Frontend:
  - HTML5 & CSS3 (Pure Vanilla CSS, custom HSL color palettes, no external CSS frameworks).
  - ES6+ JavaScript (Raw client-side DOM control, Audio API integration, state machines).
- Database & Storage:
  - JSON & JSONL flat-files (No-SQL approach designed for offline durability).
  - Data structure includes student indexes, question pools, and adaptive reports.


3. DEEP-DIVE DIRECTORY STRUCTURE
--------------------------------
- .codex/
  - memory/           : System memories, logs of resolved issues, and development lessons.
  - rules/            : Operational decision rules (AG_DECISION_RULES.md, playbooks).
  - scripts/          : Python scripts for local backup and configuration sync.
  - skills/           : Specific instructions for UI redesign, stitch, and operator tasks.
- 1. LEVEL A/         : Curriculums, vocabulary, sentence structures, and listening exercises for Level A.
- 2. LEVEL B/         : Curriculums, vocabulary, sentence structures, and listening exercises for Level B.
- 3. LEVEL C/         : Curriculums, vocabulary, sentence structures, and listening exercises for Level C.
- DATA/
  - Logs/             : Server execution traces and runtime debug outputs.
  - Student/          : Student indexes (students_index.json) and history logs.
- DOCS/
  - INFO/             : Design components, grading metrics, and guides (QUY_CHUAN_LEVEL_ABC.md).
  - UI/               : Design assets and layouts.
- ENGINE/
  - launcher_modules/ : Modular Flask route definitions, TTS utilities, and templates.
  - static/           : Frontend assets, shared dependencies, and runtime libraries.
  - wsr_audit.py      : Static checking utility to verify UTF-8 encoding and syntax safety.
- QBank/
  - pool_A_v3.jsonl   : Database containing Level A questions.
  - pool_B_v3.jsonl   : Database containing Level B questions.
  - pool_C_v3.jsonl   : Database containing Level C questions.
  - index_exam_pool.json: Questions lookup table and index maps.
- Template/
  - UltiTemp.html     : Ultimate teaching slide template containing presentation engines.
  - QTemp.html        : Standardized quiz rendering template.
  - AdaptiveTemp.html : Layout template for adaptive exam sessions.
  - DashboardTemp.html: Blueprint file used to compile the master student dashboard.
- Tools/
  - ToolListening.html: Audio comprehension exercise generator.
  - ToolQuiz.html     : Multi-mode quiz application.
  - ToolSlide.html    : Interactive slide creator and presentation application.
  - ToolExam.html     : Secure examination client.
  - ToolAdaptive.html : Dynamic exam engine linked to the adaptive assessment service.
  - ToolGame.html     : Main portal (Lobby) linking to gamified modes.
  - Castle.html       : "Castle Defense" style gamified vocabulary challenges.
  - Battle.html       : "RPG Battle" style grammar challenges.
  - ToolQBankImport.html: GUI for validating and inserting raw questions into QBank jsonl.


4. CORE INTERACTIVE TOOLS
-------------------------
- ToolListening (TL):
  - Orchestrates interactive listening exams.
  - Auto-parses raw speech data and binds to edge-tts generated voice tracks.
  - Supports sound playback controls, speed adjustments, and repeat constraints.
- ToolQuiz (TQ):
  - Dynamically extracts, renders, and grades multiple-choice questions.
  - Provides instant feedback overlays, detailed explanations, and score tracking.
- ToolSlide (TS):
  - Renders multi-step slides using markdown-like configurations or structured JSON.
  - Interactive teacher navigation with layout adaptation for projector screens.
- ToolExam (TE):
  - Runs in a locked mode to prevent students from exiting or reloading during exams.
  - Saves exam sessions directly to DATA/Student/ directory.
- ToolAdaptive (TA):
  - Interacts with launcher_modules/adaptive_runtime_core.py.
  - Employs difficulty-scaling algorithms: shifts to harder questions upon correct answers, 
    lowers difficulty on consecutive errors.
  - Outputs detailed progress metrics and exports visual PDF report cards.
- ToolQBankImport (TQI):
  - Web interface designed to batch import txt/csv question banks.
  - Validates JSON schemas, deduplicates questions, and outputs standardized jsonl rows.
- Gamified Learning (GL, GC, GB):
  - ToolGame.html (GL) serves as the main lobby.
  - Castle.html (GC) and Battle.html (GB) utilize game-loop logic to convert repetitive 
    vocabulary memorization and grammar drills into interactive gameplay.
  - Exempt from standard DEC Master UI layout constraints to permit custom game designs.


5. LAUNCHER & SERVER (DukeLauncher.pyw)
----------------------------------------
- Core Execution Model:
  - Binds Flask server to 127.0.0.1 on Port 6868.
  - Launches in background: automatically checks if port 6868 is occupied.
  - Employs ctypes Windows API to hide command prompt console instantly upon load.
  - Pins a system tray icon using pystray for quick manual restarts or shutdowns.
- Development Startup:
  - Use Start_DEC.bat at the project root for active development and daily testing.
  - Start_DEC.bat runs ENGINE/DukeLauncher.pyw directly from source without rebuilding DEC.exe.
  - DEC.exe and the PyInstaller build flow are removed from the active workflow.
  - Runtime opens in Chromium App Mode by default, not native WebView2.
  - Long-term product direction is webapp-first, with DukeLauncher.pyw acting as a local development server.
  - Install launcher dependencies from ENGINE/requirements/requirements-launcher.txt via Tools/LibraryInstall.bat.
- Master Dashboard Compilation:
  - On startup, DukeLauncher checks for updates across levels A, B, and C.
  - Combines files with DashboardTemp.html to regenerate DukeEnglishCenter.html.
  - Performs non-blocking async compiles to prevent startup lag.
- REST API Endpoints:
  - /api/update_dashboard    : Triggers compile cycle of the dashboard file.
  - /api/save_slide_html     : Saves modified slide layouts directly to the disk.
  - /generate_html           : Dynamically compiles listening lessons based on configs.
  - /generate_quiz           : Compiles a localized quiz page from selected questions.
  - /generate_slide          : Compiles slides utilizing UltiTemp.html markup.
  - /generate_adaptive_exam  : Builds a session-bound adaptive test page.
  - /start, /answer, /stop   : Endpoints to monitor and process adaptive exam actions.
  - /api/restart             : Restarts the server backend gracefully.
- Startup Architecture Transition (Before vs After):
  - Legacy (Browser-Hosted):
    - Algorithm: launcher -> server -> browser external -> app-mode window.
    - Environment: Runs in user's Coc Coc browser. Process is browser.exe. Bounded to Coc Coc cache, profile, and dark mode setting.
    - Identity: OS sees Coc Coc window. Split system tray (DukeLauncher.exe) and taskbar icon (browser).
  - New (Native-Hosted):
    - Algorithm: launcher -> server -> native WebView window -> render localhost.
    - Environment: Runs in dedicated, isolated DEC app environment. WebView2 acts as an internal rendering engine. Process is DukeLauncher.exe, using background msedgewebview2.exe.
    - Identity: OS sees "Duke English Center" app. System tray and taskbar icons share the identical DEC identity with dedicated profile at DATA\WebViewProfile.
  - Conclusion:
    - Core shift from browser-hosted web app to native-hosted app. DukeLauncher.exe now fully owns the window lifecycle, resolving blurry taskbar icons and Coc Coc dark mode overrides.


6. DESIGN STANDARDS (DEC Master UI - DMU)
------------------------------------------
To ensure a premium UX/UI and eliminate design drift, all non-game tools must implement 
the DEC Master UI specs:
- Standard Container Layout:
  - Width: max-width: 900px, centered (margin: 0 auto 20px).
  - Border Radius: 22px for containers, 18px for content cards.
  - Shadow: 0 22px 50px rgba(28, 62, 95, 0.16) for clean depth.
  - Accent Bar: 6px height at top of containers.
- Color & Typography:
  - Primary font: "Be Vietnam Pro" (mandatory). Legacy fonts are banned.
  - Colors are HSL-mapped to support dynamic dark/light adjustments without layout shifting.
- Dual Theme Synchronization:
  - Youth Theme: Playful, utilizes gradients, pink (#e91e63) to cyan (#00acc1) accents.
  - Elegant Theme: Sleek, high-contrast, professional styling for older learners.
  - Theme transitions must use standard geometry variables to prevent jitter.
- CSS Coding Rules:
  - Banned: Inline styles (style="..."), direct javascript style mutation (.style.display).
  - Banned: Sora font family, dashed/dotted borders (only solid borders are allowed).
  - Visibility control must use CSS utility classes (.hidden, .is-hidden).


7. DEVELOPMENT WORKFLOWS & SECURITY
-----------------------------------
- Local Git Rules:
  - Conventional Commits only (e.g. feat(scope): message, fix(scope): message).
  - Keep commit messages under 10 words.
- Static Guard Verification:
  - StaticGuard checks the integrity of core system HTMLs (DukeEnglishCenter.html, Templates).
  - Prevents mutation of system assets outside authorized APIs.
  - wsr_audit.py must be run before any deployment to verify UTF-8 encoding (no mojibake) 
    and validate Python/JavaScript syntax.
- Cleanup & Backup Workflows:
  - Temp files are cleared regularly.
  - Full backup is automated via `backup dec` shortcuts, archiving files into zip archives 
    stored on separate drives while excluding .git, envs, and temporary structures.
