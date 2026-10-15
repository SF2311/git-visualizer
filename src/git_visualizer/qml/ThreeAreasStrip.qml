import QtQuick

// The Three Areas strip: Working Tree and Staging Area columns, changed files only.
// The History above is the third area (its HEAD commit is highlighted there).
Rectangle {
    id: root

    required property var liveView

    readonly property real padding: 28

    color: Theme.stripBackground

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 2
        color: Theme.stripDivider
    }

    FileColumn {
        title: "Working Tree"
        files: root.liveView.workingTreeFiles
        x: root.padding
        y: root.padding
        width: root.width / 2 - root.padding * 1.5
        height: root.height - root.padding * 2
    }

    Rectangle {
        x: root.width / 2 - width / 2
        y: root.padding
        width: 2
        height: root.height - root.padding * 2
        color: Theme.stripDivider
    }

    FileColumn {
        title: "Staging Bereich"
        files: root.liveView.stagingAreaFiles
        x: root.width / 2 + root.padding / 2
        y: root.padding
        width: root.width / 2 - root.padding * 1.5
        height: root.height - root.padding * 2
    }
}
