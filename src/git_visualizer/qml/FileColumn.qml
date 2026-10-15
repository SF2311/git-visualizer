import QtQuick

// One column of the Three Areas strip: a title and the changed files below it.
Item {
    id: root

    required property string title
    required property var files

    Text {
        id: titleText
        anchors.left: parent.left
        anchors.top: parent.top
        text: root.title
        color: Theme.text
        font.pixelSize: Theme.areaTitleFontSize
        font.bold: true
    }

    Text {
        visible: fileList.count === 0
        anchors.left: parent.left
        anchors.top: titleText.bottom
        anchors.topMargin: 14
        text: "keine Änderungen"
        color: Theme.mutedText
        font.pixelSize: Theme.fileFontSize
        font.italic: true
    }

    ListView {
        id: fileList
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: titleText.bottom
        anchors.topMargin: 14
        anchors.bottom: parent.bottom
        clip: true
        spacing: 8
        interactive: false
        model: root.files

        delegate: FileEntry {
            width: ListView.view.width
        }
    }
}
