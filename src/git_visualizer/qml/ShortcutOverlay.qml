import QtQuick

// Overlay listing all keyboard shortcuts (toggled with `?`).
Rectangle {
    id: root

    required property var shortcuts

    readonly property real padding: 36 * Theme.zoom
    readonly property real keyColumnWidth: 130 * Theme.zoom

    color: Theme.overlayScrim

    Rectangle {
        anchors.centerIn: parent
        width: content.width + 2 * root.padding
        height: content.height + 2 * root.padding
        radius: 16 * Theme.zoom
        color: Theme.overlayFill

        Column {
            id: content
            anchors.centerIn: parent
            spacing: 14 * Theme.zoom

            Text {
                text: "Tastenkürzel"
                color: Theme.text
                font.pixelSize: Theme.overlayTitleFontSize
                font.bold: true
                bottomPadding: 8 * Theme.zoom
            }

            Repeater {
                model: root.shortcuts

                delegate: Row {
                    id: entry

                    required property var modelData

                    spacing: 24 * Theme.zoom

                    Item {
                        width: root.keyColumnWidth
                        height: keyCap.height

                        Rectangle {
                            id: keyCap
                            width: keyText.implicitWidth + 24 * Theme.zoom
                            height: keyText.implicitHeight + 10 * Theme.zoom
                            radius: 6 * Theme.zoom
                            color: Theme.keyFill

                            Text {
                                id: keyText
                                anchors.centerIn: parent
                                text: entry.modelData.keys
                                color: Theme.text
                                font.pixelSize: Theme.overlayFontSize
                                font.bold: true
                            }
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: entry.modelData.description
                        color: Theme.text
                        font.pixelSize: Theme.overlayFontSize
                    }
                }
            }
        }
    }
}
