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

    // Hidden fallback: the watcher normally refreshes the Live View on its own.
    Shortcut {
        sequence: "F5"
        onActivated: window.liveView.notifyRepositoryChanged()
    }

    HistoryView {
        id: history
        liveView: window.liveView
        visible: window.liveView.isRepository
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * 2 / 3
    }

    WaitingForRepository {
        visible: !window.liveView.isRepository
        anchors.centerIn: parent
        folder: window.liveView.repositoryPath
    }
}
