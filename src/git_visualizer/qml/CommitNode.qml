import QtQuick

// One commit: a ring in its lane color (merge commits with a filled center), the short
// hash (small) and below it the first message line (larger).
Item {
    id: root

    required property string shortHash
    required property string subject
    required property int colorIndex
    required property bool isMerge
    // A Ghost Commit (no longer reachable) stays where it was, faded.
    required property bool isGhost
    property real centerX
    property real centerY
    // The HEAD commit is highlighted: the History is the third of the Three Areas.
    property bool isHead: false

    // A commit the model reports as added (addedCommitHashes) grows in when created.
    property bool grows: false
    property real growth: 1

    readonly property color laneColor: Theme.branchColor(colorIndex)

    x: centerX - Theme.columnWidth / 2
    y: centerY - Theme.commitRadius
    width: Theme.columnWidth
    height: subjectText.y + subjectText.height
    opacity: Math.min(1, growth * 1.5) * ghostFade
    property real ghostFade: isGhost ? Theme.ghostOpacity : 1
    Behavior on ghostFade {
        NumberAnimation { duration: Motion.fadeDuration; easing.type: Easing.InOutQuad }
    }
    transform: Scale {
        origin.x: root.width / 2
        origin.y: Theme.commitRadius
        xScale: root.growth
        yScale: root.growth
    }

    // Existing commits slide when the layout shifts (new lanes, History scrolling left).
    Behavior on centerX {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }
    Behavior on centerY {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }

    NumberAnimation on growth {
        id: growIn
        running: false
        from: 0
        to: 1
        duration: Motion.growDuration
        easing.type: Easing.OutBack
    }

    Component.onCompleted: {
        if (grows) {
            growth = 0
            growIn.start()
        }
    }

    // Soft shadow beneath the ring.
    Rectangle {
        x: circle.x
        y: circle.y + 3 * Theme.zoom
        width: circle.width
        height: circle.height
        radius: width / 2
        color: Theme.commitShadow
        opacity: 0.12
    }

    Rectangle {
        visible: root.isHead
        anchors.centerIn: circle
        width: circle.width + 18
        height: width
        radius: width / 2
        color: "transparent"
        border.color: Theme.headCommitHalo
        border.width: 4
    }

    Rectangle {
        id: circle
        anchors.horizontalCenter: parent.horizontalCenter
        width: Theme.commitRadius * 2
        height: width
        radius: width / 2
        color: Theme.commitFill
        border.color: root.laneColor
        border.width: 6 * Theme.zoom

        Rectangle {
            visible: root.isMerge
            anchors.centerIn: parent
            width: parent.width * 0.38
            height: width
            radius: width / 2
            color: root.laneColor
        }
    }

    Rectangle {
        id: hashChip
        anchors.top: circle.bottom
        anchors.topMargin: 8 * Theme.zoom
        anchors.horizontalCenter: parent.horizontalCenter
        width: hashText.implicitWidth + 12
        height: hashText.implicitHeight + 4
        radius: 6
        color: Qt.tint(Theme.background, Qt.alpha(root.laneColor, 0.14))

        Text {
            id: hashText
            anchors.centerIn: parent
            text: root.shortHash
            color: Theme.mutedText
            font.family: "monospace"
            font.pixelSize: Theme.hashFontSize
        }
    }

    // Backing so edges passing below the commit don't run through the message.
    Rectangle {
        anchors.centerIn: subjectText
        width: subjectText.contentWidth + 12
        height: subjectText.contentHeight + 4
        radius: 6
        color: Theme.background
        opacity: 0.9
    }

    Text {
        id: subjectText
        anchors.top: hashChip.bottom
        anchors.topMargin: 4
        anchors.horizontalCenter: parent.horizontalCenter
        width: Theme.columnWidth - 16
        horizontalAlignment: Text.AlignHCenter
        text: root.subject
        color: Theme.text
        font.pixelSize: Theme.subjectFontSize
        elide: Text.ElideRight
        maximumLineCount: 2
        wrapMode: Text.Wrap
    }
}
