import QtQuick

// The legend (toggled with `L`): explains the visual language of the Live View to
// students. Every sample is the real component with made-up data, so the legend
// always looks like the Live View, in both themes and at every zoom.
Rectangle {
    id: root

    objectName: "legend"

    readonly property real padding: 36 * Theme.zoom
    readonly property real sectionSpacing: 56 * Theme.zoom
    readonly property real entrySpacing: 18 * Theme.zoom
    readonly property real wideSampleWidth: 400 * Theme.zoom
    // Shrinks the card when the window is too small for it (like FittedHistory).
    readonly property real fitScale: Math.min(1, (width - 32) / card.width, (height - 32) / card.height)

    color: Theme.overlayScrim

    component SectionTitle: Text {
        color: Theme.text
        font.pixelSize: Theme.areaTitleFontSize
        font.bold: true
        bottomPadding: 4 * Theme.zoom
    }

    // A sample commit in the History, without the HistoryView around it.
    component SampleCommit: Item {
        id: sampleCommit

        property string shortHash: "a1b2c3d"
        property string subject: ""
        property bool isGhost: false
        property bool isHead: false

        width: Theme.columnWidth
        height: commit.height

        CommitNode {
            id: commit
            shortHash: sampleCommit.shortHash
            subject: sampleCommit.subject
            colorIndex: 0
            isMerge: false
            isGhost: sampleCommit.isGhost
            isHead: sampleCommit.isHead
            centerX: Theme.columnWidth / 2
            centerY: Theme.commitRadius
        }
    }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: content.width + 2 * root.padding
        height: content.height + 2 * root.padding
        scale: root.fitScale
        radius: 16 * Theme.zoom
        color: Theme.overlayFill

        Column {
            id: content
            anchors.centerIn: parent
            spacing: 20 * Theme.zoom

            Text {
                text: "Legende"
                color: Theme.text
                font.pixelSize: Theme.overlayTitleFontSize
                font.bold: true
            }

            Row {
                spacing: root.sectionSpacing

                Column {
                    spacing: root.entrySpacing

                    SectionTitle { text: "History" }

                    LegendEntry {
                        description: "HEAD zeigt auf einen Branch: der nächste Commit verschiebt diesen Branch."

                        Column {
                            width: parent.width
                            spacing: Theme.labelSpacing
                            HeadMarker { anchors.horizontalCenter: parent.horizontalCenter }
                            BranchLabel {
                                anchors.horizontalCenter: parent.horizontalCenter
                                name: "main"
                                colorIndex: 0
                                upstream: ""
                                ahead: -1
                                behind: -1
                            }
                        }
                    }

                    LegendEntry {
                        description: "Detached HEAD (umrandet): HEAD zeigt direkt auf einen Commit, z. B. während eines Rebase. Der orange Ring markiert den HEAD-Commit."

                        Column {
                            width: parent.width
                            spacing: Theme.labelSpacing
                            HeadMarker {
                                anchors.horizontalCenter: parent.horizontalCenter
                                detached: true
                            }
                            SampleCommit {
                                anchors.horizontalCenter: parent.horizontalCenter
                                subject: "Login"
                                isHead: true
                            }
                        }
                    }

                    LegendEntry {
                        description: "Branch: ein lokaler Branch, in der Farbe seiner Linie."

                        BranchLabel {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "feature"
                            colorIndex: 1
                            upstream: ""
                            ahead: -1
                            behind: -1
                        }
                    }

                    LegendEntry {
                        description: "Remote-tracking Branch (umrandet): Stand des Remote beim letzten fetch, pull oder push."

                        RemoteTrackingLabel {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "origin/main"
                            colorIndex: 0
                        }
                    }

                    LegendEntry {
                        description: "Branch mit Upstream: ↑2 eigene Commits noch nicht gepusht, ↓1 Commit des Upstream noch nicht übernommen."

                        BranchLabel {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "main"
                            colorIndex: 0
                            upstream: "origin/main"
                            ahead: 2
                            behind: 1
                        }
                    }

                    LegendEntry {
                        description: "Ghost Commit (blass): nicht mehr erreichbar, z. B. nach Rebase, commit -\u2060-\u2060amend oder branch -\u2060D. Esc blendet ihn aus."

                        SampleCommit {
                            shortHash: "9f8e7d6"
                            subject: "Alter Commit"
                            isGhost: true
                        }
                    }
                }

                Column {
                    spacing: root.entrySpacing

                    SectionTitle { text: "Merge und Rebase" }

                    LegendEntry {
                        sampleWidth: root.wideSampleWidth
                        description: "Ein Merge oder Rebase ist pausiert und wartet auf das Lösen der Konflikte."

                        OperationBanner {
                            text: "Merge läuft – 2 Konflikte"
                            conflictCount: 2
                        }
                    }

                    LegendEntry {
                        sampleWidth: root.wideSampleWidth
                        description: "Keine Konflikte (mehr): weiter mit -\u2060-\u2060continue, abbrechen mit -\u2060-\u2060abort."

                        OperationBanner {
                            text: "Rebase 2/5"
                            conflictCount: 0
                        }
                    }

                    LegendEntry {
                        sampleWidth: root.wideSampleWidth
                        description: "Konflikt: Datei auflösen, dann mit git add in den Staging Bereich übernehmen."

                        FileEntry {
                            width: root.wideSampleWidth
                            path: "login.py"
                            change: "modified"
                            originalPath: ""
                            conflicted: true
                        }
                    }

                    SectionTitle {
                        text: "Working Tree und Staging Bereich"
                        topPadding: 12 * Theme.zoom
                    }

                    Repeater {
                        model: [
                            { path: "notizen.txt", change: "untracked", originalPath: "",
                              description: "Neue Datei, die git noch nicht verfolgt." },
                            { path: "login.py", change: "new", originalPath: "",
                              description: "Neue Datei, mit git add hinzugefügt." },
                            { path: "README.md", change: "modified", originalPath: "",
                              description: "Geänderte Datei." },
                            { path: "alt.py", change: "deleted", originalPath: "",
                              description: "Gelöschte Datei." },
                            { path: "neu.py", change: "renamed", originalPath: "alt.py",
                              description: "Umbenannte Datei (alt → neu)." }
                        ]

                        delegate: LegendEntry {
                            id: changeEntry

                            required property var modelData

                            sampleWidth: root.wideSampleWidth
                            description: modelData.description

                            FileEntry {
                                width: root.wideSampleWidth
                                path: changeEntry.modelData.path
                                change: changeEntry.modelData.change
                                originalPath: changeEntry.modelData.originalPath
                                conflicted: false
                            }
                        }
                    }

                    Text {
                        width: root.wideSampleWidth + 24 * Theme.zoom + 340 * Theme.zoom
                        text: "Eine Datei, die nach git add erneut geändert wurde, steht in beiden Spalten."
                        color: Theme.mutedText
                        font.pixelSize: Theme.overlayFontSize
                        font.italic: true
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }
}
