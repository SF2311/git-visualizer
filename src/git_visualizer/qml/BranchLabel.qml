import QtQuick

// A branch label attached to the commit the branch points to, in the branch's color.
// A branch with an Upstream also shows ahead/behind, e.g. "↑2 ↓1".
Rectangle {
    id: root

    required property string name
    required property int colorIndex
    required property string upstream
    required property int ahead
    required property int behind

    readonly property bool showsAheadBehind: upstream !== "" && ahead >= 0 && behind >= 0
    readonly property real gap: 10 * Theme.zoom
    readonly property real counterWidth: showsAheadBehind ? gap + counterText.implicitWidth : 0

    width: Math.min(labelText.implicitWidth + counterWidth + 28 * Theme.zoom, Theme.labelMaxWidth)
    height: Theme.labelHeight
    radius: 8
    color: Theme.branchColor(colorIndex)

    Row {
        anchors.centerIn: parent
        spacing: root.gap

        Text {
            id: labelText
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, root.width - 16 * Theme.zoom - root.counterWidth)
            elide: Text.ElideRight
            text: root.name
            color: Theme.branchText
            font.pixelSize: Theme.labelFontSize
            font.bold: true
        }

        Text {
            id: counterText
            visible: root.showsAheadBehind
            anchors.verticalCenter: parent.verticalCenter
            text: "↑" + root.ahead + " ↓" + root.behind
            color: Theme.branchText
            font.pixelSize: Theme.aheadBehindFontSize
            font.bold: true
        }
    }
}
