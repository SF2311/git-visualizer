import QtQuick

// Keyboard-only projector controls (no toolbars, no buttons): zoom, light/dark theme
// and the shortcut overlay. Place it last in the window so the overlay is on top.
Item {
    id: root

    objectName: "projectorControls"

    readonly property real minimumZoom: 0.5
    readonly property real maximumZoom: 3.0
    readonly property real zoomStep: 1.1

    readonly property real zoom: Theme.zoom
    readonly property bool darkTheme: Theme.dark
    property bool shortcutOverlayVisible: false

    // Every keyboard shortcut of the Live View, as listed in the overlay.
    // A ticket that adds a shortcut (e.g. Esc, L) adds its entry here.
    readonly property var shortcuts: [
        { keys: "Strg +", description: "Vergrößern" },
        { keys: "Strg −", description: "Verkleinern" },
        { keys: "Strg 0", description: "Originalgröße" },
        { keys: "T", description: "Helles / dunkles Design umschalten" },
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

    ShortcutOverlay {
        anchors.fill: parent
        visible: root.shortcutOverlayVisible
        shortcuts: root.shortcuts
    }
}
