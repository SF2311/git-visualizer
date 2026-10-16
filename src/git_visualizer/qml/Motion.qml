pragma Singleton
import QtQuick

// Timing of the Live View animations: slow enough to follow on a projector,
// short enough that the next git command never waits for the view.
QtObject {
    // Branch/tag labels, HEAD, commits and edges sliding to their new place.
    readonly property int slideDuration: 650
    readonly property int slideEasing: Easing.InOutCubic
    // A new commit growing into the graph while its edges are drawn towards it.
    readonly property int growDuration: 700
    // A removed branch or tag label fading out where it was.
    readonly property int fadeDuration: 900

    // File transitions.
    // A file sliding between the Working Tree and the Staging Area columns.
    readonly property int fileSlideDuration: 750
    // A file flying from its column into the new commit node.
    readonly property int fileFlightDuration: 950
    // Several files start one after another, spread over this span.
    readonly property int fileStaggerSpan: 300
    // A file appearing in or disappearing from a column.
    readonly property int fileFadeDuration: 450
    // The new commit grows in only after the files have arrived in it.
    readonly property int commitGrowthDelay: fileFlightDuration + fileStaggerSpan

    // The In-progress Operation banner fading in and out and changing color.
    readonly property int bannerDuration: 250
}
