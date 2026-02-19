# YouTube Downloader

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A modern, cross-platform desktop application to download YouTube videos and music with rich metadata embedding. The program provides a clean graphical interface built with CustomTkinter and leverages powerful libraries like `yt-dlp`, `PyAV`, and `mutagen` to deliver high-quality downloads.

## Features

- **Download Music** – Extract audio from YouTube videos or music streams.
  - Automatically embeds metadata: title, artist, album, year, cover art, and lyrics (when available from captions).
  - Optional conversion to MP3 (with ID3 tags) – M4A original is removed after conversion.
- **Download Video** – Fetch the best available video and audio streams and merge them into a single MP4 file.
- **Simple GUI** – Two tabs for music/video, folder selection, and real‑time status updates.
- **Threaded Downloads** – The interface remains responsive during downloads.
- **Portable** – Can be run as a Python script or packaged into a standalone EXE.

## How It Works

1. **User Input** – The user pastes a YouTube URL into the appropriate tab and optionally selects a save folder.
2. **Backend Selection** – The `YouTubeDownloader` class delegates to either `MusicDownloader` or `VideoDownloader`.
3. **Music Download**:
   - `yt-dlp` downloads the best available audio (preferring M4A).
   - Thumbnails are fetched via HTTP and embedded using `mutagen` (MP4 tags; later copied to MP3 if needed).
   - If lyrics are available in the video's automatic captions or subtitles, they are downloaded and added to the metadata.
   - If MP3 conversion is enabled, the M4A file is transcoded with `PyAV` (192 kbps) and the metadata is copied.
4. **Video Download**:
   - `yt-dlp` analyzes available formats and selects the highest quality video‑only and audio‑only streams.
   - Both streams are downloaded separately.
   - `PyAV` merges them into a single MP4 container without re‑encoding.
5. **Result** – The final file is saved in the chosen folder, and the GUI shows a success message.

## Libraries Used

| Library | Purpose |
|---------|---------|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | YouTube video/audio extraction |
| [`PyAV`](https://github.com/PyAV-Org/PyAV) | Audio/video conversion and merging |
| [`mutagen`](https://github.com/quodlibet/mutagen) | Metadata embedding (ID3, MP4) |
| [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) | Modern GUI widgets |
| [`Pillow`](https://python-pillow.org/) | Image processing (WebP → JPEG conversion) |
| [`requests`](https://docs.python-requests.org/) | Fetching thumbnails and lyrics |

## Installation

### Option 1: Run from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/youtube-downloader.git
   cd youtube-downloader
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python gui.py
   ```

### Option 2: Standalone EXE (Windows)

Pre‑built executables are available in the [Releases](https://github.com/yourusername/youtube-downloader/releases) section. Download the `.exe` file and run it – no Python installation required.

To build your own EXE with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "path/to/yt-dlp;yt_dlp" gui.py
```
(Adjust paths according to your environment.)

## Usage

1. Launch the application.
2. Click **Browse** to change the download folder (default is your system's Downloads folder).
3. Switch to the **YouTube Music** or **YouTube Video** tab.
4. Paste a valid YouTube URL into the entry field.
5. Click **Download MP3** or **Download MP4**.
6. Wait for the download to complete – a progress bar indicates activity.
7. A message box will confirm success and show the saved file name.

## Building the Executable

To create a standalone executable for Windows, use PyInstaller:

```bash
pyinstaller --onefile --windowed --name "YouTubeDownloader" gui.py
```

Make sure all dependencies are installed. The `--windowed` flag prevents a console window from appearing. You may need to include additional hidden imports (e.g., `yt_dlp`, `av`, `mutagen`, `PIL`, `customtkinter`). A complete `.spec` file can be provided upon request.

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests. Please follow the existing code style and include comments where appropriate.

## Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) – the backbone of all downloads.
- [PyAV](https://github.com/PyAV-Org/PyAV) – seamless multimedia handling.
- [mutagen](https://github.com/quodlibet/mutagen) – robust tagging library.
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – beautiful modern UI.

---

**Enjoy downloading!** If you encounter any problems, please report them on the [issue tracker](https://github.com/yourusername/youtube-downloader/issues).
