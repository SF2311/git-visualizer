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

    Shortcut {
        sequence: "Esc"
        onActivated: window.liveView.clearGhostCommits()
    }

    FittedHistory {
        id: history
        liveView: window.liveView
        visible: window.liveView.isRepository
        anchors.left: parent.left
        anchors.right: remoteBoxes.left
        anchors.top: parent.top
        // Room for the In-progress Operation banner, so it never covers the History.
        anchors.topMargin: banner.reservedHeight
        height: parent.height * 2 / 3 - banner.reservedHeight
    }

    RemoteBoxes {
        id: remoteBoxes
        liveView: window.liveView
        visible: window.liveView.isRepository
        width: visible ? implicitWidth : 0
        anchors.right: parent.right
        anchors.top: history.top
        height: history.height
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

    OperationBanner {
        id: banner
        text: window.liveView.operationBanner
        conflictCount: window.liveView.conflictCount
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: Theme.bannerMargin
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
