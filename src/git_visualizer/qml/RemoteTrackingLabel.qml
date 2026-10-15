import QtQuick

// A Remote-tracking Branch (e.g. origin/main): an outlined label, colored like the
// local branch whose Upstream it is (gray when it is nobody's Upstream).
Rectangle {
    id: root

    required property string name
    required property int colorIndex

    readonly property color outline: Theme.branchColor(colorIndex)

    width: Math.min(labelText.implicitWidth + 28 * Theme.zoom, Theme.labelMaxWidth)
    height: Theme.labelHeight
    radius: 8
    color: Theme.remoteTrackingFill
    border.color: outline
    border.width: Theme.remoteTrackingBorderWidth

    // Moves only after the lecturer fetches, pulls or pushes; then it slides.
    Behavior on x {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }
    Behavior on y {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }

    Text {
        id: labelText
        anchors.centerIn: parent
        width: Math.min(implicitWidth, root.width - 16 * Theme.zoom)
        elide: Text.ElideRight
        text: root.name
        color: root.outline
        font.pixelSize: Theme.labelFontSize
        font.bold: true
    }
}
