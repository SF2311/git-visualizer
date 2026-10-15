import QtQuick

// One changed file: a colored badge with its kind of change, then the path.
Rectangle {
    id: root

    required property string path
    required property string change
    required property string originalPath
    required property bool conflicted

    readonly property var changeLabels: ({
        "untracked": "untracked",
        "new": "neu",
        "modified": "geändert",
        "deleted": "gelöscht",
        "renamed": "umbenannt"
    })
    readonly property var changeColors: ({
        "untracked": Theme.changeUntracked,
        "new": Theme.changeNew,
        "modified": Theme.changeModified,
        "deleted": Theme.changeDeleted,
        "renamed": Theme.changeRenamed
    })

    height: Theme.fileRowHeight
    radius: 8
    color: Theme.fileFill
    border.color: root.conflicted ? Theme.conflict : Theme.fileBorder
    border.width: root.conflicted ? 3 : 1

    Rectangle {
        id: badge
        anchors.left: parent.left
        anchors.leftMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        width: badgeText.implicitWidth + 16
        height: parent.height - 14
        radius: 6
        color: root.conflicted ? Theme.conflict : (root.changeColors[root.change] ?? Theme.mutedText)

        Text {
            id: badgeText
            anchors.centerIn: parent
            text: root.conflicted ? "Konflikt" : (root.changeLabels[root.change] ?? root.change)
            color: "#ffffff"
            font.pixelSize: Theme.changeFontSize
            font.bold: true
        }
    }

    Text {
        anchors.left: badge.right
        anchors.leftMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        text: root.originalPath !== "" ? root.originalPath + " → " + root.path : root.path
        color: Theme.text
        font.family: "monospace"
        font.pixelSize: Theme.fileFontSize
        font.strikeout: root.change === "deleted"
        elide: Text.ElideMiddle
    }
}
