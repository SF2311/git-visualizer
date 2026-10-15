pragma Singleton
import QtQuick

// Colors and sizes of the Live View. `dark` and `zoom` are set by ProjectorControls
// (keys T and Ctrl +/−); every size below scales with `zoom`.
QtObject {
    property bool dark: false
    property real zoom: 1.0

    readonly property color background: dark ? "#161a22" : "#fafaf7"
    readonly property color text: dark ? "#e8ebf2" : "#1d2330"
    readonly property color mutedText: dark ? "#9aa3b2" : "#6b7280"
    readonly property color edge: dark ? "#5c6577" : "#9aa3b2"
    readonly property color commitFill: dark ? "#232937" : "#ffffff"
    readonly property color commitBorder: dark ? "#6f9cf5" : "#3b6fd8"
    readonly property color branchFill: dark ? "#4d7fe6" : "#3b6fd8"
    readonly property color branchText: "#ffffff"
    readonly property color headFill: dark ? "#f0652a" : "#d9480f"
    readonly property color headText: "#ffffff"
    readonly property color overlayScrim: dark ? "#cc000000" : "#99000000"
    readonly property color overlayFill: dark ? "#232937" : "#ffffff"
    readonly property color keyFill: dark ? "#323a4b" : "#eef1f6"

    readonly property real columnWidth: 220 * zoom
    readonly property real commitRadius: 24 * zoom
    readonly property real labelHeight: 40 * zoom
    readonly property real labelSpacing: 10 * zoom

    readonly property int hashFontSize: Math.round(15 * zoom)
    readonly property int subjectFontSize: Math.round(22 * zoom)
    readonly property int labelFontSize: Math.round(20 * zoom)
    readonly property int overlayTitleFontSize: Math.round(30 * zoom)
    readonly property int overlayFontSize: Math.round(22 * zoom)

    // Three Areas strip (ticket 04)
    readonly property color stripBackground: dark ? "#1c212b" : "#f0efe9"
    readonly property color stripDivider: dark ? "#3a4252" : "#d6d4cc"
    readonly property color fileFill: dark ? "#232937" : "#ffffff"
    readonly property color fileBorder: dark ? "#3a4252" : "#d6d4cc"
    readonly property color changeUntracked: dark ? "#51cf66" : "#2f9e44"
    readonly property color changeNew: dark ? "#51cf66" : "#2f9e44"
    readonly property color changeModified: dark ? "#fcc419" : "#e8a317"
    readonly property color changeDeleted: dark ? "#ff6b6b" : "#c92a2a"
    readonly property color changeRenamed: dark ? "#9775fa" : "#7048e8"
    readonly property color conflict: dark ? "#ff6b6b" : "#e03131"
    readonly property color headCommitHalo: headFill
    readonly property int areaTitleFontSize: Math.round(24 * zoom)
    readonly property int fileFontSize: Math.round(20 * zoom)
    readonly property int changeFontSize: Math.round(15 * zoom)
    readonly property real fileRowHeight: 40 * zoom
}
