import os
import threading
from pathlib import Path
from typing import Iterable

import pygame
from pydub import AudioSegment
from pydub.playback import play

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer, ListItem, ListView, ProgressBar, Static

FILE_EXTENSIONS = ['.mp3', '.wav', '.ogg']


class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.is_dir() and not path.name.startswith(".")]


class MusicPlayer(App):
    CSS_PATH = "riff.tcss"
    BINDINGS = [("q", "app.quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.current_track = None
        self.selected_directory = None
        self.player_thread = None

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                FilteredDirectoryTree(".", id="albums"),
                ListView(id="tracks"),
            ),
            Vertical(
                Static(' ', id="now-playing"),
                Horizontal(
                    Static("0:00", id="current-time"),
                    ProgressBar(total=100, id="progress", show_percentage=False),
                    Static("0:00", id="total-duration"),
                    id="progress-container",
                ),
                id="player",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_directory = event.path  # Store the selected directory path
        tracks = [
            file.name
            for file in Path(self.selected_directory).iterdir()
            if file.is_file() and file.suffix.lower() in FILE_EXTENSIONS
        ]
        self.query_one("#tracks").clear()
        for track in tracks:
            self.query_one("#tracks").append(ListItem(Static(track)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_track = str(event.item.children[0].render())
        self.query_one("#now-playing").update(selected_track)
        # full_path = Path(self.selected_directory) / selected_track


if __name__ == "__main__":
    app = MusicPlayer()
    app.run()
