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

    HistoryView {
        id: history
        liveView: window.liveView
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * 2 / 3
    }
}
