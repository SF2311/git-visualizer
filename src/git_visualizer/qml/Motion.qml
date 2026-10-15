pragma Singleton
import QtQuick

// Timing of the History transitions (ticket 05): slow enough to follow on a projector,
// short enough that the next git command never waits for the view.
QtObject {
    // Branch/tag labels, HEAD, commits and edges sliding to their new place.
    readonly property int slideDuration: 650
    readonly property int slideEasing: Easing.InOutCubic
    // A new commit growing into the graph while its edges are drawn towards it.
    readonly property int growDuration: 700
    // A removed branch or tag label fading out where it was.
    readonly property int fadeDuration: 900
}
