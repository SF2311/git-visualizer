import QtQuick

// Plays the model's file transitions above the window: on `add` a file slides from the
// Working Tree into the Staging Area, on unstaging back, and on `commit` the files fly
// into the new commit node (which grows in after they arrived, see HistoryView).
// Appearing and disappearing files are faded by FileColumn itself.
//
// The model announces transitions (transitionsChanged) before it updates the file
// lists: the files' old places are taken then, their new places once the lists have
// changed. Flights are separate objects, so a following refresh never cuts them short.
Item {
    id: root

    objectName: "fileFlights"

    required property var liveView
    required property var workingTree
    required property var stagingArea
    required property var history

    function column(area) {
        return area === "workingTree" ? root.workingTree : root.stagingArea
    }

    function prepare(transitions) {
        const flights = []
        for (const transition of transitions) {
            if (transition.kind !== "fileMoved" && transition.kind !== "fileCommitted")
                continue
            const source = column(transition.fromArea).sourceEntry(transition.path, root)
            if (!source)
                continue
            let revealIn = null
            if (transition.kind === "fileMoved") {
                const destination = column(transition.toArea)
                // A new entry stays hidden until the file arrives; an existing one
                // (a partially staged file) stays visible and receives it.
                if (!destination.sourceEntry(transition.path, root)) {
                    destination.hide(transition.path)
                    revealIn = destination
                }
            }
            flights.push({ "transition": transition, "source": source, "revealIn": revealIn })
        }
        if (flights.length > 0)
            Qt.callLater(() => root.launch(flights))
    }

    function launch(flights) {
        flights.forEach((flight, index) => {
            const transition = flight.transition
            const intoCommit = transition.kind === "fileCommitted"
            let target = null
            if (intoCommit) {
                const center = root.history.commitPoint(transition.toHash, root)
                target = center ? Qt.rect(center.x, center.y, 0, 0) : null
            } else {
                target = column(transition.toArea).entryRect(transition.path, root)
            }
            if (!target) {
                if (flight.revealIn)
                    flight.revealIn.reveal(transition.path)
                return
            }
            const source = flight.source
            flightComponent.createObject(root, {
                "path": source.path,
                "change": source.change,
                "originalPath": source.originalPath,
                "conflicted": source.conflicted,
                "source": source.rect,
                "target": target,
                "intoCommit": intoCommit,
                "startDelay": flights.length > 1 ? Motion.fileStaggerSpan * index / (flights.length - 1) : 0,
                "revealIn": flight.revealIn
            })
        })
    }

    Component {
        id: flightComponent
        FileFlight {}
    }

    Connections {
        target: root.liveView
        function onTransitionsChanged() {
            root.prepare(root.liveView.fileTransitions)
        }
    }
}
