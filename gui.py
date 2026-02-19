# gui.py
"""
Graphical user interface for YouTube Downloader using CustomTkinter.
"""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from downloader import YouTubeDownloader

# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("550x320")
        self.resizable(False, False)

        # Center the window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')

        # Default download folder is the user's Downloads directory
        self.folder_path = str(Path.home() / "Downloads")
        self.downloader = None

        self.create_widgets()

    def create_widgets(self):
        """Build all UI components."""
        self.title_label = ctk.CTkLabel(
            self,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=(15, 10))

        # Folder selection frame
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(fill="x", padx=20, pady=5)

        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            placeholder_text="Save folder",
            width=400
        )
        self.folder_entry.insert(0, self.folder_path)
        self.folder_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.folder_button = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            width=70,
            command=self.choose_folder,
            fg_color="#3b3b3b",
            hover_color="#505050"
        )
        self.folder_button.pack(side="right")

        # Tab view for music and video
        self.tab_view = ctk.CTkTabview(self, width=500, height=180)
        self.tab_view.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_music = self.tab_view.add("YouTube Music")
        self.create_music_tab()

        self.tab_video = self.tab_view.add("YouTube Video")
        self.create_video_tab()

    def create_music_tab(self):
        """Build the music download tab."""
        # URL entry
        self.url_music_entry = ctk.CTkEntry(
            self.tab_music,
            placeholder_text="Paste YouTube Music / YouTube URL...",
            width=400
        )
        self.url_music_entry.pack(pady=(15, 10), padx=10)

        # Download button
        self.download_music_btn = ctk.CTkButton(
            self.tab_music,
            text="Download MP3",
            command=self.start_music_download,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.download_music_btn.pack(pady=5)

        # Status label
        self.status_music_label = ctk.CTkLabel(
            self.tab_music,
            text="Ready to download music",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.status_music_label.pack(pady=(10, 0), padx=10)

    def create_video_tab(self):
        """Build the video download tab."""
        self.url_video_entry = ctk.CTkEntry(
            self.tab_video,
            placeholder_text="Paste YouTube video URL...",
            width=400
        )
        self.url_video_entry.pack(pady=(15, 10), padx=10)

        self.download_video_btn = ctk.CTkButton(
            self.tab_video,
            text="Download MP4",
            command=self.start_video_download,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.download_video_btn.pack(pady=5)

        self.status_video_label = ctk.CTkLabel(
            self.tab_video,
            text="Ready to download video",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.status_video_label.pack(pady=(10, 0), padx=10)

    def choose_folder(self):
        """Open folder selection dialog and update the entry."""
        folder = filedialog.askdirectory(initialdir=self.folder_path)
        if folder:
            self.folder_path = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def start_music_download(self):
        """Initiate music download in a background thread."""
        url = self.url_music_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        self.download_music_btn.configure(state="disabled")
        self.status_music_label.configure(text="Starting music download...")
        self.progressbar = ctk.CTkProgressBar(self.tab_music, mode="indeterminate")
        self.progressbar.pack(pady=5)
        self.progressbar.start()

        self.downloader = YouTubeDownloader(self.folder_path, convert_to_mp3=True)
        thread = threading.Thread(target=self.music_download_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def music_download_thread(self, url):
        """Background task for music download."""
        try:
            result = self.downloader.download_music(url)
            self.after(0, self.music_download_finished, result)
        except Exception as e:
            self.after(0, self.music_download_error, str(e))

    def music_download_finished(self, result):
        """Handle successful or failed music download (GUI thread)."""
        self.progressbar.stop()
        self.progressbar.destroy()
        self.download_music_btn.configure(state="normal")
        if result['success']:
            self.status_music_label.configure(text=f"✓ Downloaded: {result['filename']}")
            self.url_music_entry.delete(0, "end")
            messagebox.showinfo("Success", f"Song '{result['title']}' saved!")
        else:
            self.status_music_label.configure(text="✗ Error")
            messagebox.showerror("Error", f"Download failed:\n{result['error']}")

    def music_download_error(self, error_msg):
        """Handle exceptions during music download."""
        self.progressbar.stop()
        self.progressbar.destroy()
        self.download_music_btn.configure(state="normal")
        self.status_music_label.configure(text="✗ Error")
        messagebox.showerror("Error", f"Download failed:\n{error_msg}")

    def start_video_download(self):
        """Initiate video download in a background thread."""
        url = self.url_video_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        self.download_video_btn.configure(state="disabled")
        self.status_video_label.configure(text="Starting video download...")
        self.progressbar = ctk.CTkProgressBar(self.tab_video, mode="indeterminate")
        self.progressbar.pack(pady=5)
        self.progressbar.start()

        self.downloader = YouTubeDownloader(self.folder_path)
        thread = threading.Thread(target=self.video_download_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def video_download_thread(self, url):
        """Background task for video download."""
        try:
            result = self.downloader.download_video(url)
            self.after(0, self.video_download_finished, result)
        except Exception as e:
            self.after(0, self.video_download_error, str(e))

    def video_download_finished(self, result):
        """Handle successful or failed video download (GUI thread)."""
        self.progressbar.stop()
        self.progressbar.destroy()
        self.download_video_btn.configure(state="normal")
        if result['success']:
            self.status_video_label.configure(text=f"✓ Downloaded: {result['filename']}")
            self.url_video_entry.delete(0, "end")
            messagebox.showinfo("Success", f"Video '{result['title']}' saved!")
        else:
            self.status_video_label.configure(text="✗ Error")
            messagebox.showerror("Error", f"Download failed:\n{result['error']}")

    def video_download_error(self, error_msg):
        """Handle exceptions during video download."""
        self.progressbar.stop()
        self.progressbar.destroy()
        self.download_video_btn.configure(state="normal")
        self.status_video_label.configure(text="✗ Error")
        messagebox.showerror("Error", f"Download failed:\n{error_msg}")


if __name__ == "__main__":
    app = App()
    app.mainloop()