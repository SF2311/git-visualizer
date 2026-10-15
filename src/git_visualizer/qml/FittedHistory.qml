import QtQuick

// The History, auto-fitted to the space it gets: when the commits are wider than the
// window or the lanes taller than it, the History shrinks (down to `minimumFitScale`);
// beyond that, or when zoomed in, HistoryView keeps the newest commits visible and the
// oldest leave on the left.
Item {
    id: root

    objectName: "history"

    required property var liveView

    readonly property real minimumFitScale: 0.6
    // Fit the unzoomed History, so that Ctrl +/− still enlarges or shrinks on top of it.
    readonly property real fitScale: {
        const neededWidth = history.contentWidth / Theme.zoom + 2 * history.margin
        const neededHeight = history.contentHeight / Theme.zoom + history.margin
        if (width <= 0 || height <= 0)
            return 1.0
        return Math.max(minimumFitScale, Math.min(1.0, width / neededWidth, height / neededHeight))
    }

    clip: true

    HistoryView {
        id: history
        liveView: root.liveView
        width: root.width / root.fitScale
        height: root.height / root.fitScale
        transformOrigin: Item.TopLeft
        scale: root.fitScale
    }
}
