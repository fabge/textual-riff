# textual riff

[![PyPI - Version](https://img.shields.io/pypi/v/textual-riff.svg)](https://pypi.org/project/textual-riff)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/textual-riff.svg)](https://pypi.org/project/textual-riff)

A terminal music player written in Python using [Textual](https://github.com/textualize/textual/).

![screenshot](assets/riff.png)

## features

- Control the player with previous (p), next (n), and pause (space)
- Play music from a folder of your choice (`riff .`)
- Supports MP3, and OGG audio
- Private, no data is collected by riff

## installation

```console
pip install textual-riff
```

## usage

```console
riff .
```

## known bugs/issues

- `self.current_track` is not set properly when using the next/previous track bindings.
