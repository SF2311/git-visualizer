import QtQuick
import QtQuick.Window

Window {
    id: window

    required property var liveView

    width: 1280
    height: 800
    visible: true
    title: "Git Visualizer"
    color: Theme.background

    // Temporary manual refresh until the watcher (ticket 02) exists.
    Shortcut {
        sequence: "F5"
        onActivated: window.liveView.notifyRepositoryChanged()
    }

    FittedHistory {
        id: history
        liveView: window.liveView
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * 2 / 3
    }

    ThreeAreasStrip {
        liveView: window.liveView
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: history.bottom
        anchors.bottom: parent.bottom
    }

    // Keep last: its shortcut overlay must cover everything above.
    ProjectorControls {
        anchors.fill: parent
    }
}
