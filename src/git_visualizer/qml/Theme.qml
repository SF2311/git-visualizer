pragma Singleton
import QtQuick

// Colors and sizes of the Live View. Light theme only for now (ticket 10 adds dark + zoom).
QtObject {
    readonly property color background: "#fafaf7"
    readonly property color text: "#1d2330"
    readonly property color mutedText: "#6b7280"
    readonly property color edge: "#9aa3b2"
    readonly property color commitFill: "#ffffff"
    readonly property color commitBorder: "#3b6fd8"
    readonly property color commitShadow: "#1d2330"
    readonly property color branchFill: "#3b6fd8"
    readonly property color branchText: "#ffffff"
    readonly property color headFill: "#d9480f"
    readonly property color headText: "#ffffff"
    readonly property color tagFill: "#e5e7eb"
    readonly property color tagBorder: "#c4c9d2"
    readonly property color tagText: "#4b5563"
    readonly property color collapsedFill: "#eef0f3"

    // Branch colors, indexed by the model's colorIndex (size = branch_colors.PALETTE_SIZE).
    // Kept clear of the HEAD orange and the tag gray.
    readonly property var branchColors: [
        "#3b6fd8", "#2f9e44", "#ae3ec9", "#0c8599",
        "#b08900", "#c2255c", "#5c940d", "#6741d9"
    ]
    // Commits and edges that belong to no branch (colorIndex -1).
    readonly property color noBranch: "#9aa3b2"

    function branchColor(index) {
        return index >= 0 ? branchColors[index % branchColors.length] : noBranch
    }

    readonly property real columnWidth: 220
    readonly property real commitRadius: 24
    readonly property real commitTextHeight: 96
    readonly property real laneGap: 24
    readonly property real edgeWidth: 5
    readonly property real labelHeight: 40
    readonly property real labelSpacing: 10
    readonly property real labelMaxWidth: columnWidth - 16

    readonly property int hashFontSize: 15
    readonly property int subjectFontSize: 22
    readonly property int labelFontSize: 20
}
