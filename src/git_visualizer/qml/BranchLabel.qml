import QtQuick

// A branch label attached to the commit the branch points to.
Rectangle {
    id: root

    required property string name

    width: labelText.implicitWidth + 28
    height: Theme.labelHeight
    radius: 8
    color: Theme.branchFill

    Text {
        id: labelText
        anchors.centerIn: parent
        text: root.name
        color: Theme.branchText
        font.pixelSize: Theme.labelFontSize
        font.bold: true
    }
}
