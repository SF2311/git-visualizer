import QtQuick
import QtQuick.Shapes

// An edge from a parent commit (x1, y1) to a child commit (x2, y2). Between lanes it
// bends within one column: next to the parent where a branch forks off (first parent),
// next to the child where a merge joins in (further parents).
Shape {
    id: root

    property real x1
    property real y1
    property real x2
    property real y2
    property bool bendNearParent: true
    property bool dashed: false
    property color strokeColor: Theme.edge
    // An edge to a newly added commit is drawn from the parent towards it on creation.
    property bool grows: false
    property real growth: 1

    // Where the drawn edge ends: the child, or on its way there while growing.
    readonly property real endX: x1 + (x2 - x1) * growth
    readonly property real endY: y1 + (y2 - y1) * growth

    Behavior on x1 {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }
    Behavior on y1 {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }
    Behavior on x2 {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }
    Behavior on y2 {
        NumberAnimation { duration: Motion.slideDuration; easing.type: Motion.slideEasing }
    }

    NumberAnimation on growth {
        id: growIn
        running: false
        from: 0
        to: 1
        duration: Motion.growDuration
        easing.type: Easing.OutCubic
    }

    Component.onCompleted: {
        if (grows) {
            growth = 0
            growIn.start()
        }
    }

    readonly property real bendWidth: Math.min(Math.abs(endX - x1), Theme.columnWidth * 0.8)
    readonly property real bendStartX: bendNearParent ? x1 : endX - bendWidth
    readonly property real bendEndX: bendNearParent ? x1 + bendWidth : endX

    preferredRendererType: Shape.CurveRenderer

    ShapePath {
        strokeColor: root.strokeColor
        strokeWidth: Theme.edgeWidth
        strokeStyle: root.dashed ? ShapePath.DashLine : ShapePath.SolidLine
        dashPattern: [1.5, 1.5]
        fillColor: "transparent"
        capStyle: ShapePath.RoundCap
        joinStyle: ShapePath.RoundJoin
        startX: root.x1
        startY: root.y1

        PathLine { x: root.bendStartX; y: root.y1 }
        PathCubic {
            x: root.bendEndX
            y: root.endY
            control1X: (root.bendStartX + root.bendEndX) / 2
            control1Y: root.y1
            control2X: (root.bendStartX + root.bendEndX) / 2
            control2Y: root.endY
        }
        PathLine { x: root.endX; y: root.endY }
    }
}
