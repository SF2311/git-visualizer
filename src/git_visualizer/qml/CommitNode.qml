import QtQuick

// One commit: circle with short hash (small) above the first message line (larger).
Item {
    id: root

    required property string shortHash
    required property string subject
    property real centerX
    property real centerY
    // The HEAD commit is highlighted: the History is the third of the Three Areas.
    property bool isHead: false

    x: centerX - Theme.columnWidth / 2
    y: centerY - Theme.commitRadius
    width: Theme.columnWidth
    height: subjectText.y + subjectText.height

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
        border.color: Theme.commitBorder
        border.width: 5
    }

    Text {
        id: hashText
        anchors.top: circle.bottom
        anchors.topMargin: 10
        anchors.horizontalCenter: parent.horizontalCenter
        text: root.shortHash
        color: Theme.mutedText
        font.family: "monospace"
        font.pixelSize: Theme.hashFontSize
    }

    Text {
        id: subjectText
        anchors.top: hashText.bottom
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
