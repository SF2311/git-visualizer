import QtQuick

// HEAD as its own marker, attached to a branch label (or to a commit when detached).
Rectangle {
    width: headText.implicitWidth + 24
    height: Theme.labelHeight
    radius: height / 2
    color: Theme.headFill

    Text {
        id: headText
        anchors.centerIn: parent
        text: "HEAD"
        color: Theme.headText
        font.pixelSize: Theme.labelFontSize
        font.bold: true
    }
}
