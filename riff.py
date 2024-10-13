import os
import threading
from pathlib import Path
from typing import Iterable

import pygame
from pydub import AudioSegment
from pydub.playback import play
from mutagen import File as MutagenFile

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
                    ProgressBar(total=100, id="progress", show_percentage=False, show_eta=False),
                    Static("", id="total-duration"),  # Remove the default "0:00"
                    id="progress-container",
                ),
                id="player",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        pygame.mixer.init()  # Initialize pygame mixer

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_directory = event.path
        tracks = []
        for file in Path(self.selected_directory).iterdir():
            if file.is_file() and file.suffix.lower() in FILE_EXTENSIONS:
                full_path = str(file)
                audio = MutagenFile(full_path)
                if audio is not None:
                    length_seconds = audio.info.length
                    length_formatted = f"{int(length_seconds // 60)}:{int(length_seconds % 60):02d}"
                    tracks.append((file.name, length_formatted))

        # Sort tracks alphabetically by filename
        tracks.sort(key=lambda x: x[0].lower())

        self.query_one("#tracks").clear()
        for track, length in tracks:
            list_item = ListItem(
                Horizontal(
                    Static(track, classes="track-name"),
                    Static(length, classes="track-length")
                )
            )
            self.query_one("#tracks").append(list_item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_track = str(event.item.children[0].children[0].render())
        self.query_one("#now-playing").update(selected_track)
        full_path = Path(self.selected_directory) / selected_track
        
        # Get the total duration from the file
        audio = MutagenFile(str(full_path))
        if audio is not None:
            length_seconds = audio.info.length
            length_formatted = f"{int(length_seconds // 60)}:{int(length_seconds % 60):02d}"
            self.query_one("#total-duration").update(length_formatted)

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()
