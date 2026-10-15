import QtQuick

// Shown while the observed folder is not (yet) a git repository.
Column {
    id: root

    required property string folder

    spacing: 16

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 12

        Text {
            text: "Kein Repository – warte auf"
            color: Theme.text
            font.pixelSize: Theme.subjectFontSize * 1.4
        }
        Text {
            text: "git init"
            color: Theme.text
            font.pixelSize: Theme.subjectFontSize * 1.4
            font.family: "monospace"
            font.bold: true
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: root.folder
        color: Theme.mutedText
        font.pixelSize: Theme.hashFontSize
        font.family: "monospace"
    }
}
