import QtQuick

// A copy of one file entry on its way: sliding from one column of the Three Areas
// strip into the other (``target`` is the entry's new place), or flying into a new
// commit node and vanishing there (``intoCommit``; ``target`` is the node's center).
// Created by FileFlights; destroys itself when it has arrived.
Item {
    id: root

    property string path
    property string change
    property string originalPath
    property bool conflicted
    property rect source
    property rect target
    property bool intoCommit: false
    property int startDelay: 0
    // The column whose hidden entry for ``path`` is revealed on arrival (or null).
    property var revealIn: null

    readonly property real targetX: intoCommit ? target.x - width / 2 : target.x
    readonly property real targetY: intoCommit ? target.y - height / 2 : target.y
    readonly property int duration: intoCommit ? Motion.fileFlightDuration : Motion.fileSlideDuration

    x: source.x
    y: source.y
    width: source.width
    height: source.height

    function land() {
        if (revealIn) {
            revealIn.reveal(path)
            revealIn = null
        }
        destroy()
    }

    // Also when destroyed early (e.g. window closed): never leave an entry hidden.
    Component.onDestruction: {
        if (revealIn)
            revealIn.reveal(path)
    }

    // Lifted off the strip: a soft shadow below the moving copy.
    Rectangle {
        x: 0
        y: 4 * Theme.zoom
        width: parent.width
        height: parent.height
        radius: 8
        color: Theme.commitShadow
        opacity: 0.18
    }

    FileEntry {
        width: parent.width
        path: root.path
        change: root.change
        originalPath: root.originalPath
        conflicted: root.conflicted
    }

    SequentialAnimation {
        running: true
        PauseAnimation { duration: root.startDelay }
        ParallelAnimation {
            NumberAnimation {
                target: root
                property: "x"
                to: root.targetX
                duration: root.duration
                easing.type: root.intoCommit ? Easing.InOutQuad : Easing.InOutCubic
            }
            // Into a commit the file first slides sideways, then shoots up: a curved path.
            NumberAnimation {
                target: root
                property: "y"
                to: root.targetY
                duration: root.duration
                easing.type: root.intoCommit ? Easing.InCubic : Easing.InOutCubic
            }
            NumberAnimation {
                target: root
                property: "width"
                to: root.intoCommit ? root.width : root.target.width
                duration: root.duration
                easing.type: Easing.InOutCubic
            }
            SequentialAnimation {
                NumberAnimation {
                    target: root
                    property: "scale"
                    to: root.intoCommit ? 0.9 : 1.06
                    duration: root.duration * 0.3
                    easing.type: Easing.OutQuad
                }
                NumberAnimation {
                    target: root
                    property: "scale"
                    to: root.intoCommit ? 0.15 : 1
                    duration: root.duration * 0.7
                    easing.type: Easing.InCubic
                }
            }
            SequentialAnimation {
                PauseAnimation { duration: root.intoCommit ? root.duration * 0.65 : root.duration }
                NumberAnimation {
                    target: root
                    property: "opacity"
                    to: root.intoCommit ? 0 : 1
                    duration: root.intoCommit ? root.duration * 0.35 : 0
                }
            }
        }
        ScriptAction { script: root.land() }
    }
}
