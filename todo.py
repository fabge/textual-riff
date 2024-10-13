
   def play_track(self, track_path: str) -> None:
        if self.current_track:
            pygame.mixer.music.stop()

        try:
            print(f"Playing track: {track_path}")
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            self.current_track = track_path

            self.query_one("#now-playing").update(f"Now Playing: {Path(track_path).name}")
            self.query_one("#progress").update(progress=0)
            self.set_interval(0.1, self.update_progress)
        except pygame.error as e:
            self.query_one("#now-playing").update(f"Error: {str(e)}")

    def update_progress(self) -> None:
        if pygame.mixer.music.get_busy():
            try:
                current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
                sound = pygame.mixer.Sound(self.current_track)
                total_length = sound.get_length()
                progress = (current_pos / total_length) * 100
                self.query_one("#progress").update(progress=progress)
            except pygame.error:
                self.cancel_update_progress()
        else:
            self.cancel_update_progress()
