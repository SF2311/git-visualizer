import QtQuick

// One Remote: name, shortened URL, when it was last fetched and its Remote-tracking
// Branches (outlined, like their labels in the History).
Rectangle {
    id: root

    required property var liveView
    required property string name
    required property string shortUrl
    required property real lastFetched
    required property var trackingBranches
    // Current time in Unix seconds, ticked by RemoteBoxes so the age stays current.
    property real now: Date.now() / 1000

    width: Theme.remoteBoxWidth
    height: content.implicitHeight + 2 * Theme.remoteBoxPadding
    radius: 12 * Theme.zoom
    color: Theme.remoteBoxFill
    border.color: Theme.remoteBoxBorder
    border.width: 2 * Theme.zoom

    Column {
        id: content
        x: Theme.remoteBoxPadding
        y: Theme.remoteBoxPadding
        width: root.width - 2 * Theme.remoteBoxPadding
        spacing: 6 * Theme.zoom

        Text {
            width: parent.width
            elide: Text.ElideRight
            text: root.name
            color: Theme.text
            font.pixelSize: Theme.remoteNameFontSize
            font.bold: true
        }

        Text {
            width: parent.width
            elide: Text.ElideMiddle
            text: root.shortUrl
            color: Theme.mutedText
            font.family: "monospace"
            font.pixelSize: Theme.remoteDetailFontSize
        }

        Text {
            width: parent.width
            elide: Text.ElideRight
            text: root.liveView.lastFetchText(root.lastFetched, root.now)
            color: Theme.mutedText
            font.pixelSize: Theme.remoteDetailFontSize
            font.italic: true
        }

        Flow {
            width: parent.width
            spacing: 6 * Theme.zoom
            topPadding: 4 * Theme.zoom

            Repeater {
                model: root.trackingBranches

                Rectangle {
                    id: chip
                    required property var modelData
                    readonly property color outline: Theme.branchColor(modelData.colorIndex)
                    width: Math.min(chipText.implicitWidth + 18 * Theme.zoom, content.width)
                    height: Theme.remoteChipHeight
                    radius: 6 * Theme.zoom
                    color: Theme.remoteTrackingFill
                    border.color: outline
                    border.width: 2 * Theme.zoom

                    Text {
                        id: chipText
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, chip.width - 12 * Theme.zoom)
                        elide: Text.ElideRight
                        text: chip.modelData.name
                        color: chip.outline
                        font.pixelSize: Theme.remoteChipFontSize
                        font.bold: true
                    }
                }
            }
        }
    }
}
