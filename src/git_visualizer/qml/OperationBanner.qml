import QtQuick

// Banner explaining the In-progress Operation ("Merge läuft – 2 Konflikte",
// "Rebase 2/5"). Red while conflicts remain, amber once they are resolved; fades
// out when the operation is completed or aborted.
Rectangle {
    id: root

    required property string text
    required property int conflictCount

    // Keeps the last text while fading out, so the banner doesn't collapse empty.
    property string shownText: ""
    onTextChanged: if (text !== "") shownText = text
    Component.onCompleted: shownText = text

    readonly property bool active: text !== ""
    // Height the window keeps free above the History while the banner is shown.
    property real reservedHeight: active ? Theme.bannerHeight + Theme.bannerMargin * 2 : 0
    Behavior on reservedHeight {
        NumberAnimation { duration: Motion.bannerDuration; easing.type: Easing.InOutQuad }
    }

    implicitWidth: label.implicitWidth + Theme.bannerPadding * 2
    implicitHeight: Theme.bannerHeight
    radius: height / 2
    color: root.conflictCount > 0 ? Theme.bannerConflictFill : Theme.bannerFill
    opacity: active ? 1 : 0
    visible: opacity > 0

    Behavior on opacity {
        NumberAnimation { duration: Motion.bannerDuration; easing.type: Easing.InOutQuad }
    }
    Behavior on color {
        ColorAnimation { duration: Motion.bannerDuration }
    }

    Text {
        id: label
        anchors.centerIn: parent
        text: root.shownText
        color: Theme.bannerText
        font.pixelSize: Theme.bannerFontSize
        font.bold: true
    }
}
