import os
import threading
import time
from pathlib import Path
from typing import Iterable

import pygame
from pydub import AudioSegment
from pydub.playback import play
from mutagen import File as MutagenFile

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer, ListItem, ListView, ProgressBar, Static
from textual.worker import Worker, WorkerState
from textual import work

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
        self.progress_worker = None

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
                    tracks.append((file.name, length_formatted, length_seconds))

        # Sort tracks alphabetically by filename
        tracks.sort(key=lambda x: x[0].lower())

        self.query_one("#tracks").clear()
        for track, length, duration in tracks:
            list_item = ListItem(
                Horizontal(
                    Static(track, classes="track-name"),
                    Static(length, classes="track-length")
                )
            )
            list_item.track_duration = duration  # Store duration in the ListItem
            self.query_one("#tracks").append(list_item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_track = str(event.item.children[0].children[0].render())
        self.query_one("#now-playing").update(selected_track)
        
        # Get the total duration from the stored value
        length_seconds = event.item.track_duration
        length_formatted = f"{int(length_seconds // 60)}:{int(length_seconds % 60):02d}"
        self.query_one("#total-duration").update(length_formatted)

        # Stop the current playback if any
        if self.player_thread:
            pygame.mixer.music.stop()
            self.player_thread.join()

        # Start playing the selected track
        full_path = os.path.join(self.selected_directory, selected_track)
        self.player_thread = threading.Thread(target=self.play_audio, args=(full_path,))
        self.player_thread.start()

        # Start updating the progress bar
        if self.progress_worker:
            self.progress_worker.cancel()
        self.progress_worker = self.update_progress(length_seconds)

    def play_audio(self, file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

    def update_progress(self, total_duration: float) -> None:
        """Update the progress bar and current time."""
        progress_bar = self.query_one("#progress")
        current_time = self.query_one("#current-time")
        
        def update_worker():
            for i in range(int(total_duration)):
                if not pygame.mixer.music.get_busy():
                    break
                progress = (i / total_duration) * 100
                time_str = f"{i // 60}:{i % 60:02d}"
                self.call_from_thread(progress_bar.update, progress=progress)
                self.call_from_thread(current_time.update, time_str)
                time.sleep(1)

        self.run_worker(update_worker, thread=True)

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()
