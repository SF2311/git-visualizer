import QtQuick

// A branch label attached to the commit the branch points to, in the branch's color.
Rectangle {
    id: root

    required property string name
    required property int colorIndex

    width: Math.min(labelText.implicitWidth + 28 * Theme.zoom, Theme.labelMaxWidth)
    height: Theme.labelHeight
    radius: 8
    color: Theme.branchColor(colorIndex)

    Text {
        id: labelText
        anchors.centerIn: parent
        width: Math.min(implicitWidth, root.width - 16)
        elide: Text.ElideRight
        text: root.name
        color: Theme.branchText
        font.pixelSize: Theme.labelFontSize
        font.bold: true
    }
}
