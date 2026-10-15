import QtQuick

// A branch or tag label that was just removed (e.g. `git branch -d`), fading out where
// it was last shown. Rows come from the model's `leavingLabels`.
Item {
    id: root

    required property string refType
    required property string name
    required property int colorIndex

    width: refType === "tag" ? tagLabel.width : branchLabel.width
    height: Theme.labelHeight
    transformOrigin: Item.Bottom

    BranchLabel {
        id: branchLabel
        visible: root.refType !== "tag"
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
