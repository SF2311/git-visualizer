import QtQuick

// The History: commits left to right by ancestry, one lane (row) per branch, with
// edges, branch/tag labels stacked above their commit, HEAD, and older history
// collapsed into "…" left of column 0. FittedHistory scales it to the window.
Item {
    id: root

    required property var liveView

    readonly property real margin: 60
    readonly property real slotHeight: Theme.labelHeight + Theme.labelSpacing
    readonly property bool truncated: root.liveView.historyTruncated
    readonly property var laneSlots: root.liveView.laneLabelSlots
    // Width of the commits plus the "…" column when older history is collapsed.
    readonly property real contentWidth: (Math.max(0, root.liveView.columnCount) + (truncated ? 1 : 0))
                                         * Theme.columnWidth
    // Left edge of column 0; keeps the newest commits visible when the History is wider
    // than the window, and leaves room for the "…" marker when history is collapsed.
    readonly property real originX: Math.min(margin + (truncated ? Theme.columnWidth : 0),
                                             width - margin - Math.max(0, root.liveView.columnCount) * Theme.columnWidth)
    // Top of each lane (relative), plus the total height as the last entry.
    readonly property var laneTops: {
        let tops = []
        let y = 0
        for (let i = 0; i < laneSlots.length; ++i) {
            tops.push(y)
            y += laneSlots[i] * slotHeight + Theme.commitRadius * 2 + Theme.commitTextHeight + Theme.laneGap
        }
        tops.push(y)
        return tops
    }
    readonly property real contentHeight: laneTops[laneTops.length - 1]
    readonly property real originY: Math.max(margin / 2, (height - contentHeight) / 2)
    // New commits that files are flying into; they grow in once the files arrived.
    readonly property var filesCommittedInto: root.liveView.fileTransitions
        .filter(transition => transition.kind === "fileCommitted")
        .map(transition => transition.toHash)

    // Center of the commit node ``hash`` (null when not shown), for files flying into it.
    function commitCenter(hash) {
        for (let i = 0; i < commitNodes.count; ++i) {
            const node = commitNodes.itemAt(i)
            if (node && node.hash === hash)
                return Qt.point(node.centerX, node.centerY)
        }
        return null
    }

    function columnCenterX(column) {
        return originX + column * Theme.columnWidth + Theme.columnWidth / 2
    }

    function laneCenterY(lane) {
        if (lane < 0 || lane >= laneSlots.length)
            return originY + Theme.commitRadius
        return originY + laneTops[lane] + laneSlots[lane] * slotHeight + Theme.labelSpacing + Theme.commitRadius
    }

    // Top edge of a label in stack slot ``slot`` above a commit in ``lane``.
    function slotY(lane, slot) {
        return laneCenterY(lane) - Theme.commitRadius - (slot + 1) * slotHeight
    }

    clip: true

    Repeater {
        model: root.liveView.laneBands

        Rectangle {
            required property int lane
            required property int colorIndex
            required property int firstColumn
            required property int lastColumn
            x: root.columnCenterX(firstColumn) - Theme.columnWidth / 2 + 10 * Theme.zoom
            width: (lastColumn - firstColumn + 1) * Theme.columnWidth - 20 * Theme.zoom
            y: root.laneCenterY(lane) - height / 2
            height: Theme.commitRadius * 2 + 20 * Theme.zoom
            radius: height / 2
            color: Qt.alpha(Theme.branchColor(colorIndex), Theme.dark ? 0.16 : 0.10)

            Behavior on x {
                NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
            }
            Behavior on y {
                NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
            }
            Behavior on width {
                NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
            }
        }
    }

    Repeater {
        model: root.liveView.edges

        HistoryEdge {
            required property string childHash
            required property int childColumn
            required property int childLane
            required property int parentColumn
            required property int parentLane
            required property int colorIndex
            required property bool toCollapsed
            required property bool firstParent
            x1: root.columnCenterX(parentColumn) + (toCollapsed ? Theme.columnWidth * 0.25 : 0)
            y1: root.laneCenterY(parentLane)
            x2: root.columnCenterX(childColumn)
            y2: root.laneCenterY(childLane)
            bendNearParent: firstParent
            dashed: toCollapsed
            strokeColor: Theme.branchColor(colorIndex)
            grows: root.liveView.addedCommitHashes.indexOf(childHash) >= 0
            growDelay: root.filesCommittedInto.indexOf(childHash) >= 0 ? Motion.commitGrowthDelay : 0
        }
    }

    // Older history collapsed into "…" where an edge leads to a hidden parent.
    Repeater {
        model: root.liveView.edges

        Rectangle {
            required property int childLane
            required property bool toCollapsed
            visible: toCollapsed
            x: root.columnCenterX(-1) - width / 2
            y: root.laneCenterY(childLane) - height / 2
            width: 64 * Theme.zoom
            height: 36 * Theme.zoom
            radius: height / 2
            color: Theme.collapsedFill
            border.color: Theme.edge
            border.width: 2

            Text {
                anchors.centerIn: parent
                text: "…"
                color: Theme.mutedText
                font.pixelSize: Theme.subjectFontSize
                font.bold: true
            }
        }
    }

    Text {
        visible: root.truncated
        x: root.columnCenterX(-1) - width / 2
        y: root.laneCenterY(0) + Theme.commitRadius + 12 * Theme.zoom
        width: Theme.columnWidth - 40 * Theme.zoom
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.Wrap
        text: root.liveView.hiddenCommitCount === 1
              ? "1 älterer Commit"
              : root.liveView.hiddenCommitCount + " ältere Commits"
        color: Theme.mutedText
        font.pixelSize: Theme.hashFontSize
    }

    Repeater {
        id: commitNodes
        model: root.liveView.commits

        CommitNode {
            required property string hash
            required property int column
            required property int lane
            isHead: hash === root.liveView.headCommitHash
            grows: root.liveView.addedCommitHashes.indexOf(hash) >= 0
            growDelay: root.filesCommittedInto.indexOf(hash) >= 0 ? Motion.commitGrowthDelay : 0
            centerX: root.columnCenterX(column)
            centerY: root.laneCenterY(lane)
        }
    }

    Repeater {
        model: root.liveView.branchLabels

        BranchLabel {
            required property int column
            required property int lane
            required property int stackIndex
            visible: column >= 0
            x: root.columnCenterX(column) - width / 2
            y: root.slotY(lane, stackIndex)
        }
    }

    Repeater {
        model: root.liveView.tagLabels

        TagLabel {
            required property int column
            required property int lane
            required property int stackIndex
            visible: column >= 0
            x: root.columnCenterX(column) - width / 2
            y: root.slotY(lane, stackIndex)
        }
    }

    // Labels of removed branches and tags fade out where they were.
    Repeater {
        model: root.liveView.leavingLabels

        LeavingLabel {
            required property int column
            required property int lane
            required property int stackIndex
            x: root.columnCenterX(column) - width / 2
            y: root.slotY(lane, stackIndex)
        }
    }

    HeadMarker {
        visible: root.liveView.headColumn >= 0
        detached: root.liveView.headDetached
        x: root.columnCenterX(root.liveView.headColumn) - width / 2
        y: root.slotY(root.liveView.headLane, root.liveView.headStackIndex)
    }
}
