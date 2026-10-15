import QtQuick

// One line of the legend: a sample built from the Live View's own components on the
// left, its German explanation on the right.
Row {
    id: root

    required property string description
    property real sampleWidth: Theme.columnWidth
    property real descriptionWidth: 340 * Theme.zoom
    // The sample, e.g. a BranchLabel with made-up data.
    default property alias sample: sampleSlot.data

    spacing: 24 * Theme.zoom

    Item {
        id: sampleSlot
        width: root.sampleWidth
        height: childrenRect.height
    }

    Text {
        anchors.verticalCenter: parent.verticalCenter
        width: root.descriptionWidth
        text: root.description
        color: Theme.text
        font.pixelSize: Theme.overlayFontSize
        wrapMode: Text.Wrap
    }
}
