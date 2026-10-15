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

    readonly property real bendWidth: Math.min(Math.abs(x2 - x1), Theme.columnWidth * 0.8)
    readonly property real bendStartX: bendNearParent ? x1 : x2 - bendWidth
    readonly property real bendEndX: bendNearParent ? x1 + bendWidth : x2

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
            y: root.y2
            control1X: (root.bendStartX + root.bendEndX) / 2
            control1Y: root.y1
            control2X: (root.bendStartX + root.bendEndX) / 2
            control2Y: root.y2
        }
        PathLine { x: root.x2; y: root.y2 }
    }
}
