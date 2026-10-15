import QtQuick

// One column of the Three Areas strip: a title and the changed files below it.
// Files fade in and out; FileFlights finds entries here (sourceEntry, entryRect) and
// hides an entry while a copy of the file is still flying towards it (hide, reveal).
Item {
    id: root

    required property string title
    required property var files

    // Paths whose entry is hidden, with how many flights are still heading there.
    property var hiddenPaths: ({})

    function hide(path) {
        const hidden = Object.assign({}, hiddenPaths)
        hidden[path] = (hidden[path] ?? 0) + 1
        hiddenPaths = hidden
    }

    function reveal(path) {
        const hidden = Object.assign({}, hiddenPaths)
        if ((hidden[path] ?? 0) > 1)
            hidden[path] -= 1
        else
            delete hidden[path]
        hiddenPaths = hidden
    }

    function _indexOf(path) {
        fileList.forceLayout()
        for (let i = 0; i < fileList.count; ++i) {
            const item = fileList.itemAtIndex(i)
            if (item && item.path === path)
                return i
        }
        return -1
    }

    // The shown entry for ``path`` as it is drawn now (rect in ``target``'s
    // coordinates plus the file's roles), or null when it is not listed or not visible.
    function sourceEntry(path, target) {
        const index = _indexOf(path)
        if (index < 0)
            return null
        const item = fileList.itemAtIndex(index)
        const topLeft = item.mapToItem(target, 0, 0)
        return {
            "rect": Qt.rect(topLeft.x, topLeft.y, item.width, item.height),
            "path": item.path,
            "change": item.change,
            "originalPath": item.originalPath,
            "conflicted": item.conflicted
        }
    }

    // Where the entry for ``path`` ends up once the list has settled, in ``target``'s
    // coordinates; null when it is not listed or below the visible part of the list.
    function entryRect(path, target) {
        const index = _indexOf(path)
        if (index < 0)
            return null
        const top = index * (Theme.fileRowHeight + fileList.spacing)
        if (top + Theme.fileRowHeight > fileList.height)
            return null
        const topLeft = fileList.contentItem.mapToItem(target, 0, top)
        return Qt.rect(topLeft.x, topLeft.y, fileList.width, Theme.fileRowHeight)
    }

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

        delegate: Item {
            id: row

            required property string path
            required property string change
            required property string originalPath
            required property bool conflicted

            width: ListView.view.width
            height: Theme.fileRowHeight

            FileEntry {
                width: parent.width
                path: row.path
                change: row.change
                originalPath: row.originalPath
                conflicted: row.conflicted
                opacity: (root.hiddenPaths[row.path] ?? 0) > 0 ? 0 : 1
            }
        }

        add: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.fileFadeDuration }
            NumberAnimation {
                property: "scale"
                from: 0.85
                to: 1
                duration: Motion.fileFadeDuration
                easing.type: Easing.OutBack
            }
        }
        remove: Transition {
            NumberAnimation { property: "opacity"; to: 0; duration: Motion.fileFadeDuration }
        }
        // Rows closing a gap or making room slide; an interrupted fade-in still completes.
        displaced: Transition {
            NumberAnimation { properties: "x,y"; duration: Motion.fileFadeDuration; easing.type: Easing.OutCubic }
            NumberAnimation { property: "opacity"; to: 1; duration: Motion.fileFadeDuration }
            NumberAnimation { property: "scale"; to: 1; duration: Motion.fileFadeDuration }
        }
    }
}
