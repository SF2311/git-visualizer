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

    // Three Areas strip (ticket 04)
    readonly property color stripBackground: "#f0efe9"
    readonly property color stripDivider: "#d6d4cc"
    readonly property color fileFill: "#ffffff"
    readonly property color fileBorder: "#d6d4cc"
    readonly property color changeUntracked: "#2f9e44"
    readonly property color changeNew: "#2f9e44"
    readonly property color changeModified: "#e8a317"
    readonly property color changeDeleted: "#c92a2a"
    readonly property color changeRenamed: "#7048e8"
    readonly property color conflict: "#e03131"
    readonly property color headCommitHalo: "#d9480f"
    readonly property int areaTitleFontSize: 24
    readonly property int fileFontSize: 20
    readonly property int changeFontSize: 15
    readonly property real fileRowHeight: 40
}
