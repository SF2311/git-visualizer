import QtQuick

// Keyboard-only projector controls (no toolbars, no buttons): zoom, light/dark theme,
// the legend and the shortcut overlay. Place it last in the window so both are on top.
Item {
    id: root

    objectName: "projectorControls"

    readonly property real minimumZoom: 0.5
    readonly property real maximumZoom: 3.0
    readonly property real zoomStep: 1.1

    readonly property real zoom: Theme.zoom
    readonly property bool darkTheme: Theme.dark
    property bool shortcutOverlayVisible: false
    property bool legendVisible: false

    // Every keyboard shortcut of the Live View, as listed in the overlay; a new
    // shortcut adds its entry here (Esc and F5 are handled in Main.qml).
    readonly property var shortcuts: [
        { keys: "Strg +", description: "Vergrößern" },
        { keys: "Strg −", description: "Verkleinern" },
        { keys: "Strg 0", description: "Originalgröße" },
        { keys: "Esc", description: "Ghost Commits ausblenden" },
        { keys: "F5", description: "Repository neu einlesen" },
        { keys: "T", description: "Helles / dunkles Design umschalten" },
        { keys: "L", description: "Legende ein- / ausblenden" },
        { keys: "?", description: "Tastenkürzel ein- / ausblenden" }
    ]

    function setZoom(value) {
        Theme.zoom = Math.min(maximumZoom, Math.max(minimumZoom, value))
    }

    Shortcut {
        sequences: [StandardKey.ZoomIn, "Ctrl+="]
        onActivated: root.setZoom(Theme.zoom * root.zoomStep)
    }

    Shortcut {
        sequences: [StandardKey.ZoomOut]
        onActivated: root.setZoom(Theme.zoom / root.zoomStep)
    }

    Shortcut {
        sequence: "Ctrl+0"
        onActivated: root.setZoom(1.0)
    }

    Shortcut {
        sequence: "T"
        onActivated: Theme.dark = !Theme.dark
    }

    Shortcut {
        sequence: "?"
        onActivated: root.shortcutOverlayVisible = !root.shortcutOverlayVisible
    }

    Shortcut {
        sequence: "L"
        onActivated: root.legendVisible = !root.legendVisible
    }

    Legend {
        anchors.fill: parent
        visible: root.legendVisible
    }

    // After the legend, so `?` also shows the shortcuts while the legend is open.
    ShortcutOverlay {
        anchors.fill: parent
        visible: root.shortcutOverlayVisible
        shortcuts: root.shortcuts
    }
}
