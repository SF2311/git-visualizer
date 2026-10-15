# Native Qt Quick (QML) GUI in Python via PySide6

The Live View is a native desktop app built with Qt Quick/QML and Python (PySide6), Linux first but kept cross-platform where it costs little. We rejected a browser served by a local process and Electron/Tauri (preference for a native app, not a webview), GTK4/libadwaita (graph animations are harder) and Rust GUI toolkits (more to build ourselves). QML was chosen for its declarative, GPU-rendered animations, which carry the teaching value of showing *what changed*.
