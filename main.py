from io import BytesIO
import random
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import os
import sys
from pygame import mixer
from PIL import Image, ImageTk
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from pydub import AudioSegment
import json  # For saving and loading settings
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from PIL import Image, ImageTk, ImageFilter

# Initialize pygame mixer for audio playback
mixer.init()

# Default folder path for music
DEFAULT_FOLDER = "G:\\Playlists\\PHONK LORDS\\Soudiere"

# Presets
reverb_presets = [
    {"name": "None", "params": None},
    {"name": "Room", "params": {"delay_ms": 100, "feedback": 0.3}},
    {"name": "Hall", "params": {"delay_ms": 200, "feedback": 0.5}},
    {"name": "Plate", "params": {"delay_ms": 150, "feedback": 0.7}},
    {"name": "Chamber", "params": {"delay_ms": 300, "feedback": 0.6}},
    {"name": "Cathedral", "params": {"delay_ms": 400, "feedback": 0.8}},
]

delay_presets = [
    {"name": "None", "params": None},
    {"name": "Short Delay", "params": {"delay_ms": 100, "feedback": 0.4}},
    {"name": "Long Delay", "params": {"delay_ms": 500, "feedback": 0.5}},
    {"name": "Ping-Pong", "params": {"delay_ms": 350, "feedback": 0.6}},
    {"name": "Slapback", "params": {"delay_ms": 75, "feedback": 0.3}},
]

equalizer_presets = [
    {"name": "Flat", "params": {"Bass": 5, "Mid": 5, "Treble": 5}},
    {"name": "Bass Boost", "params": {"Bass": 8, "Mid": 5, "Treble": 6}},
    {"name": "Treble Boost", "params": {"Bass": 5, "Mid": 5, "Treble": 8}},
    {"name": "Vocal Boost", "params": {"Bass": 4, "Mid": 8, "Treble": 7}},
    {"name": "Rock", "params": {"Bass": 7, "Mid": 6, "Treble": 8}},
]

# Load saved directory from a file
def load_saved_directory():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('music_directory', DEFAULT_FOLDER)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_FOLDER

# Save the directory
def save_directory(directory):
    settings = {'music_directory': directory}
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

# Function to scan a folder for audio files
def scan_folder_for_songs(folder_path):
    songs = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.mp3', '.flac', '.wav', '.ogg')):
                songs.append(os.path.join(root, file))
    return songs

# Music Player GUI with settings and modes
class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elevate Music Player")
        self.root.geometry("800x600")  # Modernized window size
        self.root.configure(bg="#121212")  # Dark background for the window
        self.current_mode = "Shuffle"  # Default mode: Shuffle
        self.song_index = 0  # Index of the current song
        self.songs = []  # List to store song paths
        self.favorite_songs = []  # List for favorite songs
        self.playlists = {}  # Dictionary to store playlists
        self.folder_path = load_saved_directory()  # Load the last opened directory
        self.songs = scan_folder_for_songs(self.folder_path)
        self.current_position = 0
        self.volume = 1.0  # Default volume
        self.current_song_path = ""
        self.favorite_songs = self.load_favorites()

        # Create the main frame layout
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#121212")
        self.main_frame.pack(fill="both", expand=True)
        

        # Add a left, center, and right split frame
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212")
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.center_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212")
        self.center_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212")
        self.right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        # Add video visuals to the left frame
        self.video_visuals_label = ctk.CTkLabel(self.left_frame, text="Video Visuals", text_color="white", fg_color="#121212", font=("Helvetica", 16))
        self.video_visuals_label.pack(pady=10)

        # Add a video player to the left frame
        self.video_player = tk.Frame(self.left_frame, bg="#121212")
        self.video_player.pack(fill="both", expand=True)

        self.video = tk.Label(self.video_player, bg="#121212")
        self.video.pack(fill="both", expand=True)

        # Add a scrollbar for the left frame
        self.canvas = tk.Canvas(self.left_frame, bg="#121212")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#121212")

        # Add scrollbar to the canvas
        self.scrollbar = tk.Scrollbar(self.left_frame, orient="vertical", command=self.canvas.yview, bg="#333333")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        #Show preset name
        self.preset_hint_label = ctk.CTkLabel(self.center_frame, text="", text_color="white", fg_color="#121212", font=("Helvetica", 16))
        self.preset_hint_label.pack(pady=10)

        self.scrollbar.pack(side="right", fill="both")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Add GUI components
        self.add_widgets()

        # Play the first song (autoplay)
        if self.songs:
            self.play_music()

        # Start the event loop to handle the end of the song
        self.root.after(100, self.check_song_end)

    def add_widgets(self):
        # Song List on the Left
        self.song_info_label = ctk.CTkLabel(self.scrollable_frame, text="Now Playing: None", text_color="white", fg_color="#121212", font=("Helvetica", 16))
        self.song_info_label.pack(pady=10)

        # Seek Slider
        self.seek_slider_label = ctk.CTkLabel(self.scrollable_frame, text="Seek:", text_color="white", font=("Helvetica", 14))
        self.seek_slider_label.pack(side="left", padx=10, pady=10)

        self.seek_slider = ctk.CTkSlider(self.scrollable_frame, from_=0, to=100, number_of_steps=100, command=self.seek_song, fg_color="#333333", bg_color="#121212", button_color="#ffffff", button_hover_color="#cccccc")
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", padx=10, pady=10)

        #Remove from favorites button
        self.favorite_button = ctk.CTkButton(self.scrollable_frame, text="Remove Favorite", command=self.remove_from_favorites, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.favorite_button.pack(side="left", padx=10, pady=10)

        # Add album art on the right
        self.album_art_label = ctk.CTkLabel(self.right_frame, text="", fg_color="#121212", text_color="white")
        self.album_art_label.pack(pady=10)

        self.load_default_album_cover()

        # Metadata label below the album art
        self.metadata_label = ctk.CTkLabel(self.right_frame, text="Metadata: None", text_color="white", fg_color="#121212", font=("Helvetica", 12))
        self.metadata_label.pack(pady=10)

        # Now Playing Queue in the center
        self.now_playing_queue_label = ctk.CTkLabel(self.center_frame, text="Now Playing Queue", text_color="white", fg_color="#121212", font=("Helvetica", 16))
        self.now_playing_queue_label.pack(pady=10)

        # Add a scrollbar for the now playing queue
        self.queue_canvas = tk.Canvas(self.center_frame, bg="#121212")
        self.queue_scrollable_frame = tk.Frame(self.queue_canvas, bg="#121212")

        # Add scrollbar to the canvas
        self.queue_scrollbar = tk.Scrollbar(self.center_frame, orient="vertical", command=self.queue_canvas.yview, bg="#333333")
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)

        self.queue_scrollbar.pack(side="right", fill="both")
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        self.queue_canvas.create_window((0, 0), window=self.queue_scrollable_frame, anchor="nw")

        self.queue_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))
        )

        # Controls frame with Play, Stop, Next, Previous, Pause, Volume Slider
        controls_frame = ctk.CTkFrame(self.root, fg_color="#121212")
        controls_frame.pack(side="bottom", fill="both", pady=10)

        # Create Buttons with hover effects
        self.play_button = ctk.CTkButton(controls_frame, text="Play", command=self.play_music, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.play_button.pack(side="left", padx=10, pady=10)

        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self.pause_or_resume, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.pause_button.pack(side="left", padx=10, pady=10)

        self.stop_button = ctk.CTkButton(controls_frame, text="Stop", command=self.stop_music, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.stop_button.pack(side="left", padx=10, pady=10)

        self.next_button = ctk.CTkButton(controls_frame, text="Next", command=self.next_song, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.next_button.pack(side="left", padx=10, pady=10)

        self.previous_button = ctk.CTkButton(controls_frame, text="Previous", command=self.previous_song, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.previous_button.pack(side="left", padx=10, pady=10)

        self.mode_button = ctk.CTkButton(controls_frame, text=f"Mode: {self.current_mode}", command=self.toggle_mode, text_color="white", width=10, hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.mode_button.pack(side="left", padx=10, pady=10)

        # Volume Slider
        volume_label = ctk.CTkLabel(controls_frame, text="Volume:", text_color="white", font=("Helvetica", 14))
        volume_label.pack(side="left", padx=10, pady=10)
        self.volume_slider = ctk.CTkSlider(controls_frame, from_=0, to=1, number_of_steps=100, command=self.set_volume, fg_color="#333333", bg_color="#121212", button_color="#ffffff", button_hover_color="#cccccc")
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side="left", padx=10, pady=10)

        # Settings Button
        self.settings_button = ctk.CTkButton(controls_frame, text="Settings", command=self.show_settings, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.settings_button.pack(side="left", padx=10, pady=10)

        # Add Favorite Button
        self.favorite_button = ctk.CTkButton(controls_frame, text="Favorite", command=self.toggle_favorite, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.favorite_button.pack(side="left", padx=10, pady=10)

        # Play Favorites Button
        self.play_favorites_button = ctk.CTkButton(controls_frame, text="Play Favorites", command=self.play_favorites, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        self.play_favorites_button.pack(side="left", padx=10, pady=10)
 
        # Manage Playlists Button
        #self.manage_playlists_button = ctk.CTkButton(controls_frame, text="Manage Playlists", command=self.manage_playlists, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        #self.manage_playlists_button.pack(side="left", padx=10, pady=10)

        # Center the buttons
        controls_frame.pack_configure(expand=True, fill="both")
        for widget in controls_frame.winfo_children():
            widget.pack_configure(expand=True)

    def get_song_metadata(self, song_path):
        try:
            # Try loading the song file with Mutagen
            if song_path.endswith('.mp3'):
                audio = MP3(song_path, ID3=ID3)
            elif song_path.endswith('.flac'):
                audio = FLAC(song_path)
            else:
                return "Unknown", "Unknown", "Unknown"  # For unsupported formats

            # Get metadata: Title, Artist, and Album
            title = audio.get('TIT2', 'Unknown Title')  # Title (Song name)
            artist = audio.get('TPE1', 'Unknown Artist')  # Artist
            album = audio.get('TALB', 'Unknown Album')  # Album

            return title.text[0] if hasattr(title, 'text') else 'Unknown Title', \
                   artist.text[0] if hasattr(artist, 'text') else 'Unknown Artist', \
                   album.text[0] if hasattr(album, 'text') else 'Unknown Album'
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return "Unknown", "Unknown", "Unknown"

    def load_default_album_cover(self):
        # Define the path for your default image
        default_image_path = "C:\\Users\\Administrator\\Downloads\\spotify-assets\\assets\\img14.jpg"  # Update this to the path where your default image is saved

        try:
            # Open the image using PIL
            img = Image.open(default_image_path)
            img = img.resize((200, 200))  # Resize it to a suitable size (optional)
            ctk_img = ctk.CTkImage(dark_image=img, light_image=img, size=(200,200))

            # Update the label with the album cover image
            self.album_art_label.configure(image=ctk_img, width=200, height=200)
            self.album_art_label.image = ctk_img  # Keep a reference to the image
        except Exception as e:
            print(f"Error loading album cover: {e}")
            self.album_art_label.configure(text="No Album Cover")

    def show_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Effect Settings")
        settings_window.geometry("300x300")
        settings_window.configure(bg="#121212")

        reverb_button = ctk.CTkButton(settings_window, text="Cycle Reverb", command=self.cycle_reverb, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        reverb_button.pack(pady=10)

        delay_button = ctk.CTkButton(settings_window, text="Cycle Delay", command=self.cycle_delay, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        delay_button.pack(pady=10)

        eq_button = ctk.CTkButton(settings_window, text="Cycle EQ", command=self.cycle_equalizer, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        eq_button.pack(pady=10)

        # New buttons to load file or folder
        load_file_button = ctk.CTkButton(settings_window, text="Load File", command=self.load_music_file, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        load_file_button.pack(pady=10)

        load_folder_button = ctk.CTkButton(settings_window, text="Load Folder", command=self.load_music_folder, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        load_folder_button.pack(pady=10)

    def load_music_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Music Files", "*.mp3;*.wav;*.flac;*.ogg")])
        if file_path:
            self.songs = [file_path]
            self.play_music()

    def load_music_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.songs = scan_folder_for_songs(folder_path)
            self.play_music()

    def show_preset_hint(self, preset_name):
        """Show the preset name as a hint text momentarily."""
        self.preset_hint_label.configure(text=f"Current preset: {preset_name}")
        self.root.after(1000, self.hide_preset_hint)  # Hide after 1 second

    def hide_preset_hint(self):
        """Hide the preset hint label."""
        self.preset_hint_label.configure(text="")

    def cycle_reverb(self):
        current_preset = reverb_presets.pop(0)
        reverb_presets.append(current_preset)
        print(f"Reverb preset changed to: {current_preset['name']}")
        self.show_preset_hint(current_preset['name'])  # Show the hint

    def cycle_delay(self):
        current_preset = delay_presets.pop(0)
        delay_presets.append(current_preset)
        print(f"Delay preset changed to: {current_preset['name']}")
        self.show_preset_hint(current_preset['name'])  # Show the hint

    def cycle_equalizer(self):
        current_preset = equalizer_presets.pop(0)
        equalizer_presets.append(current_preset)
        print(f"Equalizer preset changed to: {current_preset['name']}")
        self.show_preset_hint(current_preset['name'])  # Show the hint

    def bind_seek_slider(self):
        """Bind the seek slider to a function that updates the song position when the user changes it."""
        self.seek_slider.bind("<ButtonRelease-1>", self.on_slider_change)

    def on_slider_change(self, event):
        """Handles the change in position when the user drags the seek slider."""
        new_position = self.seek_slider.get()  # Get the new position in seconds
        self.current_position = new_position  # Update current position
        mixer.music.stop()  # Stop the current music
        mixer.music.play(start=self.current_position)  # Play from the new position
        self.update_seek_slider()  # Update the seek slider and song info labe

    def play_music(self):
        if self.songs:
            song = self.songs[self.song_index]
            mixer.music.load(song)
            if self.current_position > 0:
                mixer.music.play(start=self.current_position)  # Resume from the saved position
            else:
                mixer.music.play()
            song_info = os.path.basename(song)
            self.song_info_label.configure(text=f"Now Playing: {song_info}")

            # Get the path of the current song
            song_path = self.songs[self.song_index]
            self.current_song_path = song_path  # Store the current song path as a class attribute
            self.song_info_label.configure(text=f"Now Playing: {os.path.basename(song_path)}")

            # Set the song duration for the seek slider (update this every time a song is played)
            self.song_duration = mixer.Sound(song_path).get_length()  # Get duration in seconds
            self.seek_slider.configure(to=self.song_duration)
            
            # Get metadata (song name, artist, album)
            title, artist, album = self.get_song_metadata(song)

            # Update metadata label below the album art
            self.metadata_label.configure(text=f"Song: {title}\nArtist: {artist}\nAlbum: {album}")

            self.load_album_cover(song)

            # Update the now playing queue
            self.update_now_playing_queue()

            # Load video visuals (if available)
            self.load_video_visuals(song)

            #Mark song as is playing
            self.is_playing = True

            #Update the seek slider
            self.update_seek_slider()
    
    def get_album_cover_path(cover_name):
        # Get the path to the current folder (whether running from source or executable)
        if hasattr(sys, '_MEIPASS'):
            # Running from bundled executable (PyInstaller)
            base_path = sys._MEIPASS  # _MEIPASS is where PyInstaller unpacks the bundle
        else:
            # Running from source
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the album cover
        cover_path = os.path.join(base_path, 'album_covers', cover_name)  # 'album_covers' is the bundled folder name
        
        return cover_path

    def load_album_cover(self, song_path):
        # Get the directory of the song file
        song_directory = os.path.dirname(song_path)

        # Define possible image file names (this can be customized as needed)
        possible_image_files = ['cover.jpg', 'album_cover.jpg', 'folder_cover.jpg']

        # Try to find an image in the same directory as the song
        for image_filename in possible_image_files:
            image_path = os.path.join(song_directory, image_filename)
            if os.path.exists(image_path):
                self.display_album_cover(image_path)
                return

        # If no image is found, load the default album cover
        self.load_default_album_cover()

    def display_album_cover(self, image_path):
        try:
            # Open and display the album art image
            img = Image.open(image_path)
            img = img.resize((200, 200), Image.Resampling.LANCZOS)  # Resize to fit the label (optional)
            ctk_img = ctk.CTkImage(dark_image=img, light_image=img, size=(200,200))

            # Update the label with the album cover image
            self.album_art_label.configure(image=ctk_img, width=200, height=200)
            self.album_art_label.image = ctk_img  # Keep a reference to the image
            
        except Exception as e:
            print(f"Error loading album cover from {image_path}: {e}")
            self.load_default_album_cover()

    def load_video_visuals(self, song_path):
        # Define the path for your video file (this can be customized as needed)
        video_filename = 'Tropical - A$AP Rocky (with AK47 intro).mp4'  # Update this to the path where your video file is saved
        video_path = os.path.join(os.path.dirname(song_path), video_filename)

        if os.path.exists(video_path):
            self.display_video_visuals(video_path)
        else:
            self.video.configure(text="No Video Visuals Available")

    def display_video_visuals(self, video_path):
        try:
            import vlc
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
            self.media = self.instance.media_new(video_path)
            self.player.set_media(self.media)

            # Embed the video player in the Tkinter window
            self.player.set_hwnd(self.video.winfo_id())
            self.player.play()
        except Exception as e:
            print(f"Error loading video visuals: {e}")
            self.video.configure(text="Error Loading Video Visuals")

    def pause_or_resume(self):
        if mixer.music.get_busy():  # If music is playing
            self.current_position = mixer.music.get_pos() / 1000  # Save the current position in seconds
            mixer.music.pause()
            self.pause_button.configure(text="Resume")  # Change button text to 'Resume'
            if self.player:
                self.player.pause()
        else:
            mixer.music.unpause()
            self.pause_button.configure(text="Pause")
            if self.player:
                self.player.play()

    def stop_music(self):
        mixer.music.stop()
        self.song_info_label.configure(text="Now Playing: None")
        self.pause_button.configure(text="Pause")  # Reset pause button text to "Pause"
        self.is_playing = False
        self.seek_slider.set(0)
        if self.player:
            self.player.stop()

    def next_song(self):
        self.song_index = (self.song_index + 1) % len(self.songs)
        self.play_music()

    def previous_song(self):
        self.song_index = (self.song_index - 1) % len(self.songs)
        self.play_music()

    def set_volume(self, value):
        self.volume = value
        mixer.music.set_volume(self.volume)
        if self.player:
            self.player.audio_set_volume(int(self.volume * 100))

    def toggle_mode(self):
        if self.current_mode == "Repeat":
            self.current_mode = "Shuffle"
            self.shuffle_songs()  # Shuffle the songs
        else:
            self.current_mode = "Repeat"
            self.songs = scan_folder_for_songs(self.folder_path)  # Reset to the original order

        self.mode_button.configure(text=f"Mode: {self.current_mode}")

    def shuffle_songs(self):
        random.shuffle(self.songs)

    def load_favorites(self):
        """Load the list of favorite songs from a JSON file."""
        try:
            with open('favorites.json', 'r') as file:
                favorites = json.load(file)
            return favorites
        except FileNotFoundError:
            return []  # If the file doesn't exist, return an empty list

    def save_favorites(self):
        """Save the current list of favorite songs to a JSON file."""
        with open('favorites.json', 'w') as file:
            json.dump(self.favorite_songs, file)

    def toggle_favorite(self):
        """Add or remove a song from the favorite list."""
        current_song = self.songs[self.song_index]
        if current_song in self.favorite_songs:
            self.favorite_songs.remove(current_song)
            print(f"Removed from favorites: {os.path.basename(current_song)}")
        else:
            self.favorite_songs.append(current_song)
            print(f"Added to favorites: {os.path.basename(current_song)}")
        
        self.save_favorites()  # Save the updated favorite list

    def remove_from_favorites(self):
        """Remove a specific song from the favorite list."""
        current_song = self.songs[self.song_index]
        if current_song in self.favorite_songs:
            self.favorite_songs.remove(current_song)
            print(f"Removed from favorites: {os.path.basename(current_song)}")
            self.save_favorites()  # Save the updated list
        else:
            messagebox.showwarning("Warning", f"{os.path.basename(current_song)} is not in your favorites.")

    def play_favorites(self):
        """Play the favorite songs."""
        if self.favorite_songs:
            self.songs = self.favorite_songs
            self.song_index = 0
            self.play_music()
        else:
            print("Error: No favorite songs to play")

    def update_seek_slider(self):
        if self.is_playing:
            # Get the current position in seconds (mixer.music.get_pos() returns milliseconds)
            current_pos = mixer.music.get_pos() / 1000.0  # Convert milliseconds to seconds
            
            # Update the seek slider
            self.seek_slider.set(current_pos)

            # Update the song info label to show current position and duration
            minutes = int(current_pos // 60)
            seconds = int(current_pos % 60)
            total_minutes = int(self.song_duration // 60)
            total_seconds = int(self.song_duration % 60)
            self.song_info_label.configure(
                text=f"Now Playing: {os.path.basename(self.current_song_path)} ({minutes}:{seconds}/{total_minutes}:{total_seconds})"
            )

            # Continue updating the seek slider every 100 ms
            self.root.after(100, self.update_seek_slider)
        else:
            # Stop updating the slider if the song is not playing
            pass

    def seek_song(self, value):
        # Convert slider value (seconds) to the appropriate position in the song
        seek_position = float(value)
        
        # Set the music position using pygame.mixer.music.seek()
        mixer.music.set_pos(seek_position)

    def create_playlist(self):
        playlist_name = ctk.CTkInputDialog(text="Enter playlist name:", title="Create Playlist")
        playlist_name = playlist_name.get_input()
        if playlist_name:
            self.playlists[playlist_name] = []
            self.select_songs_for_playlist(playlist_name)

    def select_songs_for_playlist(self, playlist_name):
        songs_window = ctk.CTkToplevel(self.root)
        songs_window.title(f"Select Songs for {playlist_name}")
        songs_window.geometry("300x400")
        songs_window.configure(bg="#121212")

        # Add a frame for the top buttons
        top_buttons_frame = ctk.CTkFrame(songs_window, fg_color="#121212")
        top_buttons_frame.pack(fill="x")

        # Done Button
        done_button = ctk.CTkButton(top_buttons_frame, text="Done", command=lambda: self.add_selected_songsToPlaylist(playlist_name, songs_window), text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        done_button.pack(side="left", padx=10, pady=10)

        # Back Button
        back_button = ctk.CTkButton(top_buttons_frame, text="Back", command=songs_window.destroy, text_color="white", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
        back_button.pack(side="right", padx=10, pady=10)

        # Scrollable frame for the song list
        songs_frame = ctk.CTkScrollableFrame(songs_window, fg_color="#121212")
        songs_frame.pack(fill="both", expand=True)

        for song in self.songs:
            song_name = os.path.basename(song)
            song_var = tk.BooleanVar()
            song_checkbox = ctk.CTkCheckBox(songs_frame, text=song_name, variable=song_var, text_color="white", fg_color="#121212", hover_color="#333333", corner_radius=8, font=("Helvetica", 14))
            song_checkbox.pack(pady=5)

    def add_selected_songs_to_playlist(self, playlist_name, songs_window):
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                if widget == songs_window:
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkScrollableFrame):
                            for song_checkbox in child.winfo_children():
                                if isinstance(song_checkbox, ctk.CTkCheckBox):
                                    if song_checkbox.get():
                                        song_path = os.path.join(self.folder_path, song_checkbox.cget("text"))
                                        self.playlists[playlist_name].append(song_path)
                    print(f"Added songs to playlist: {playlist_name}")
                    songs_window.destroy()
                    break

    def load_playlist(self, playlist_name):
        if playlist_name in self.playlists:
            self.songs = self.playlists[playlist_name]
            self.play_music()
        else:
            messagebox.showerror("Error", "Playlist not found")

    def view_playlist(self, playlist_name):
        if playlist_name in self.playlists:
            playlist_window = ctk.CTkToplevel(self.root)
            playlist_window.title(f"Playlist: {playlist_name}")
            playlist_window.geometry("300x300")
            playlist_window.configure(bg="#121212")

            playlist_frame = ctk.CTkFrame(playlist_window, fg_color="#121212")
            playlist_frame.pack(fill="both", expand=True)

            for song in self.playlists[playlist_name]:
                song_name = os.path.basename(song)
                song_label = ctk.CTkLabel(playlist_frame, text=song_name, text_color="white", fg_color="#121212", font=("Helvetica", 14))
                song_label.pack(pady=5)
        else:
            messagebox.showerror("Error", "Playlist not found")

    def update_now_playing_queue(self):
        # Clear the current queue
        for widget in self.queue_scrollable_frame.winfo_children():
            widget.destroy()

        # Add the current queue
        for i, song in enumerate(self.songs):
            song_name = os.path.basename(song)
            song_label = ctk.CTkLabel(self.queue_scrollable_frame, text=song_name, text_color="white", fg_color="#121212", font=("Helvetica", 14))
            song_label.pack(pady=5)

    def check_song_end(self):
        if not mixer.music.get_busy():  # If the music has finished playing
            # Only play the next song if the music is not paused or stopped
            if self.current_mode == "Shuffle":
                self.song_index = random.randint(0, len(self.songs) - 1)  # Pick a random song index for shuffle
            else:
                self.song_index = (self.song_index + 1) % len(self.songs)  # Go to the next song in the list

            # Check if the music is still playing, if yes, don't start a new song
            if mixer.music.get_busy():
                self.play_music()  # Play the next song

        self.root.after(100, self.check_song_end)  # Check every 100ms

# Create the main window
root = ctk.CTk()

# Create the music player instance
music_player = MusicPlayer(root)

# Start the Tkinter event loop
root.mainloop()