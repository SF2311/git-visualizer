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
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * 2 / 3
    }

    ThreeAreasStrip {
        id: strip
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

    // Files sliding between the strip's columns and flying into new commits, above both.
    FileFlights {
        anchors.fill: parent
        visible: window.liveView.isRepository
        liveView: window.liveView
        workingTree: strip.workingTreeColumn
        stagingArea: strip.stagingAreaColumn
        history: history
    }

    // Keep last: its shortcut overlay must cover everything above.
    ProjectorControls {
        anchors.fill: parent
    }
}
