import QtQuick

// A branch, tag or Remote-tracking Branch label that was just removed (e.g.
// `git branch -d`, `git fetch --prune`), fading out where it was last shown. Rows come
// from the model's `leavingLabels`.
Item {
    id: root

    required property string refType
    required property string name
    required property int colorIndex

    width: refType === "tag" ? tagLabel.width
         : refType === "remoteTracking" ? remoteTrackingLabel.width
         : branchLabel.width
    height: Theme.labelHeight
    transformOrigin: Item.Bottom

    BranchLabel {
        id: branchLabel
        visible: root.refType === "branch"
        name: root.name
        colorIndex: root.colorIndex
        // A leaving label shows no ahead/behind.
        upstream: ""
        ahead: -1
        behind: -1
    }

    RemoteTrackingLabel {
        id: remoteTrackingLabel
        visible: root.refType === "remoteTracking"
        name: root.name
        colorIndex: root.colorIndex
    }

    TagLabel {
        id: tagLabel
        visible: root.refType === "tag"
        name: root.name
    }

    ParallelAnimation {
        running: true
        NumberAnimation {
            target: root
            property: "opacity"
            from: 1
            to: 0
            duration: Motion.fadeDuration
            easing.type: Easing.InQuad
        }
        NumberAnimation {
            target: root
            property: "scale"
            from: 1
            to: 0.85
            duration: Motion.fadeDuration
            easing.type: Easing.InQuad
        }
    }
}
