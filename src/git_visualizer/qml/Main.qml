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

    FittedHistory {
        id: history
        liveView: window.liveView
        visible: window.liveView.isRepository
        anchors.left: parent.left
        anchors.right: remoteBoxes.left
        anchors.top: parent.top
        height: parent.height * 2 / 3
    }

    RemoteBoxes {
        id: remoteBoxes
        liveView: window.liveView
        visible: window.liveView.isRepository
        width: visible ? implicitWidth : 0
        anchors.right: parent.right
        anchors.top: parent.top
        height: history.height
    }

    ThreeAreasStrip {
        liveView: window.liveView
        visible: window.liveView.isRepository
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: history.bottom
        anchors.bottom: parent.bottom
    }

    WaitingForRepository {
        visible: !window.liveView.isRepository
        anchors.centerIn: parent
        folder: window.liveView.repositoryPath
    }

    // Keep last: its shortcut overlay must cover everything above.
    ProjectorControls {
        anchors.fill: parent
    }
}
