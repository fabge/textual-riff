import os
import sys
import threading
import time
from pathlib import Path
from typing import Iterable

import pygame
from mutagen import File as MutagenFile

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer, ListItem, ListView, ProgressBar, Static
from textual.timer import Timer
from textual import work
from textual.message import Message

FILE_EXTENSIONS = ['.mp3', '.ogg']


class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.is_dir() and not path.name.startswith(".")]


class MusicPlayer(App):
    CSS_PATH = "riff.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_play", "Play/Pause"),
        ("n", "next_track", "Next Track"),
        ("p", "previous_track", "Previous Track"),
    ]

    def __init__(self):
        super().__init__()
        self.current_track = None
        self.selected_directory = None
        self.player_thread = None
        self.progress_timer = None
        self.start_time = None
        self.total_duration = 0
        self.is_playing = False
        self.paused_time = 0
        pygame.init()  # Initialize pygame
        pygame.mixer.init()  # Initialize pygame mixer

    def compose(self) -> ComposeResult:
        # Get the path from command line argument or use current directory
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        yield Vertical(
            Horizontal(
                FilteredDirectoryTree(path, id="albums"),
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
        pygame.mixer.music.set_endevent(pygame.USEREVENT)  # Set up end of track event
        self.set_interval(0.1, self.check_music_end)  # Check for end of track regularly

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

    def action_toggle_play(self) -> None:
        # if self.current_track: # reintroduce when `self.current_track` is not set properly when using the next/previous track bindings is fixed
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.paused_time = time.time() - self.start_time
            self.progress_timer.stop()
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.start_time = time.time() - self.paused_time
            self.progress_timer = self.set_interval(0.1, self.update_progress)

    def action_next_track(self) -> None:
        tracks_list = self.query_one("#tracks")
        current_index = tracks_list.index
        if current_index < len(tracks_list.children) - 1:
            tracks_list.index = current_index + 1
            self.on_list_view_selected(ListView.Selected(tracks_list, tracks_list.highlighted_child))

    def action_previous_track(self) -> None:
        tracks_list = self.query_one("#tracks")
        current_index = tracks_list.index
        if current_index > 0:
            tracks_list.index = current_index - 1
            self.on_list_view_selected(ListView.Selected(tracks_list, tracks_list.highlighted_child))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_track = str(event.item.children[0].children[0].render())
        self.query_one("#now-playing").update(selected_track)
        
        # Get the total duration from the stored value
        self.total_duration = event.item.track_duration
        length_formatted = f"{int(self.total_duration // 60)}:{int(self.total_duration % 60):02d}"
        self.query_one("#total-duration").update(length_formatted)

        # Stop the current playback if any
        if self.player_thread:
            pygame.mixer.music.stop()
            self.player_thread.join()

        # Cancel the current progress timer if it exists
        if self.progress_timer:
            self.progress_timer.stop()

        # Start playing the selected track
        full_path = os.path.join(self.selected_directory, selected_track)
        self.player_thread = threading.Thread(target=self.play_audio, args=(full_path,))
        self.player_thread.start()

        # Start updating the progress bar
        self.start_time = time.time()
        self.progress_timer = self.set_interval(0.1, self.update_progress)
        self.is_playing = True
        self.current_track = selected_track

    def play_audio(self, file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

    def update_progress(self) -> None:
        if not pygame.mixer.music.get_busy():
            self.progress_timer.stop()
            return

        elapsed_time = time.time() - self.start_time
        progress = (elapsed_time / self.total_duration) * 100
        time_str = f"{int(elapsed_time // 60)}:{int(elapsed_time % 60):02d}"

        self.query_one("#progress").update(progress=progress)
        self.query_one("#current-time").update(time_str)

    def check_music_end(self) -> None:
        if not pygame.mixer.music.get_busy() and self.is_playing:
            self.post_message(self.TrackEnded())

    class TrackEnded(Message):
        """A message sent when a track has ended."""

    def on_music_player_track_ended(self) -> None:
        self.action_next_track()

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()
