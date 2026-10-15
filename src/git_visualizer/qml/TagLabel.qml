import QtQuick

// A tag: a plain gray label on the commit it points to.
Rectangle {
    id: root

    required property string name

    width: Math.min(labelText.implicitWidth + 24, Theme.labelMaxWidth)
    height: Theme.labelHeight
    radius: 4
    color: Theme.tagFill
    border.color: Theme.tagBorder
    border.width: 1

    Text {
        id: labelText
        anchors.centerIn: parent
        width: Math.min(implicitWidth, root.width - 14)
        elide: Text.ElideRight
        text: root.name
        color: Theme.tagText
        font.pixelSize: Theme.labelFontSize
    }
}
