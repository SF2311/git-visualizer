import QtQuick

// The History: commits left to right, one column each, with branch labels and HEAD.
Item {
    id: root

    required property var liveView

    readonly property real margin: 60
    readonly property real commitY: height * 0.6
    readonly property real contentWidth: Math.max(0, root.liveView.columnCount) * Theme.columnWidth
    // Keep the newest commits visible when the History is wider than the window.
    readonly property real originX: Math.min(margin, width - margin - contentWidth)

    function columnCenterX(column) {
        return originX + column * Theme.columnWidth + Theme.columnWidth / 2
    }

    clip: true

    // Simple connecting line for the linear History (ticket 03 draws real edges).
    Rectangle {
        visible: root.liveView.columnCount > 1
        x: root.columnCenterX(0)
        width: (root.liveView.columnCount - 1) * Theme.columnWidth
        y: root.commitY - height / 2
        height: 4
        radius: 2
        color: Theme.edge
    }

    Repeater {
        model: root.liveView.commits

        CommitNode {
            required property int column
            centerX: root.columnCenterX(column)
            centerY: root.commitY
        }
    }

    Repeater {
        model: root.liveView.branchLabels

        BranchLabel {
            required property int column
            x: root.columnCenterX(column) - width / 2
            y: root.commitY - Theme.commitRadius - Theme.labelSpacing - height
        }
    }

    HeadMarker {
        visible: root.liveView.headColumn >= 0
        x: root.columnCenterX(root.liveView.headColumn) - width / 2
        // Attached HEAD sits on top of its branch label; detached HEAD directly on the commit.
        y: root.commitY - Theme.commitRadius - Theme.labelSpacing - height
           - (root.liveView.headDetached ? 0 : Theme.labelHeight + Theme.labelSpacing)
    }
}
