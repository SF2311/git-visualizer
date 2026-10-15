import QtQuick

// The Remote boxes at the right edge of the History, one per Remote. Zero width when
// the Observed Repository has no Remotes.
Item {
    id: root

    objectName: "remoteBoxes"

    required property var liveView

    property real now: Date.now() / 1000
    readonly property bool hasRemotes: boxes.count > 0

    implicitWidth: hasRemotes ? Theme.remoteBoxWidth + 2 * Theme.remoteBoxSpacing : 0
    clip: true

    // "vor N Min." must advance even when the repository does not change.
    Timer {
        interval: 15000
        running: root.hasRemotes
        repeat: true
        onTriggered: root.now = Date.now() / 1000
    }

    Column {
        x: Theme.remoteBoxSpacing
        y: Theme.remoteBoxSpacing
        spacing: Theme.remoteBoxSpacing

        Repeater {
            id: boxes
            model: root.liveView.remotes

            RemoteBox {
                liveView: root.liveView
                now: root.now
            }
        }
    }
}
