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
    readonly property color branchFill: "#3b6fd8"
    readonly property color branchText: "#ffffff"
    readonly property color headFill: "#d9480f"
    readonly property color headText: "#ffffff"

    readonly property real columnWidth: 220
    readonly property real commitRadius: 24
    readonly property real labelHeight: 40
    readonly property real labelSpacing: 10

    readonly property int hashFontSize: 15
    readonly property int subjectFontSize: 22
    readonly property int labelFontSize: 20
}
