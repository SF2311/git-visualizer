import QtQuick

// HEAD as its own marker with a pointer downwards: onto its branch label when attached,
// directly onto the commit when detached (then outlined, to stand apart).
Item {
    id: root

    property bool detached: false

    width: pill.width
    height: Theme.labelHeight

    // Pointer towards what HEAD points at (the label or commit below).
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height - height / 2 - 2
        width: 14 * Theme.zoom
        height: 14 * Theme.zoom
        rotation: 45
        color: Theme.headFill
    }

    Rectangle {
        id: pill
        width: headText.implicitWidth + 24 * Theme.zoom
        height: parent.height
        radius: height / 2
        color: root.detached ? Theme.background : Theme.headFill
        border.color: Theme.headFill
        border.width: 3

        Text {
            id: headText
            anchors.centerIn: parent
            text: "HEAD"
            color: root.detached ? Theme.headFill : Theme.headText
            font.pixelSize: Theme.labelFontSize
            font.bold: true
        }
    }
}
