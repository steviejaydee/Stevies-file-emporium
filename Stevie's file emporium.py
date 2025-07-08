import sys
import subprocess
import importlib.util
import os
from pathlib import Path


REQUIRED_PACKAGES = [
    ('tkinter', None), 
    ('pygame', 'pygame'),
    ('pytubefix', 'pytubefix'),
    ('requests', 'requests'),
    ('beautifulsoup4', 'beautifulsoup4'),
    ('pathlib', None), 
    ('PyPDF2', 'PyPDF2'),
    ('Pillow', 'Pillow'),
    ('moviepy', 'moviepy'),
]

def check_and_install_package(package_name, pip_name=None):
    """Check if a package is installed, and install it if not."""
    if pip_name is None:
        pip_name = package_name
    

    if package_name == 'tkinter':
        try:
            import tkinter
            return True
        except ImportError:
            print(f"Warning: tkinter is not available. This usually means Python wasn't installed with tkinter support.")
            print("Please install Python with tkinter support or install tkinter separately.")
            return False
    

    if importlib.util.find_spec(package_name) is not None:
        return True
    

    print(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}. Please install it manually using: pip install {pip_name}")
        return False
    except Exception as e:
        print(f"Error installing {package_name}: {e}")
        return False

def install_dependencies():
    """Install all required dependencies."""
    print("Checking and installing required dependencies...")
    print("=" * 50)
    
    missing_packages = []
    
    for package_name, pip_name in REQUIRED_PACKAGES:
        if not check_and_install_package(package_name, pip_name):
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nWarning: The following packages could not be installed: {', '.join(missing_packages)}")
        print("Please install them manually before running the program.")
        return False
    else:
        print("\nAll dependencies are installed successfully!")
        print("=" * 50)
        return True


if __name__ == "__main__":
    if not install_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import pygame
from pytubefix import YouTube, Playlist
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import csv
import json
from urllib.parse import urljoin, urlparse
import time
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import moviepy.editor as mp

class YouTubeConverter:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.setup_ui()
        self.download_thread = None
        
    def setup_ui(self):

        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(main_frame, textvariable=self.format_var, 
                                   values=["mp4", "mp3"], state="readonly", width=10)
        format_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Quality:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="1080p")
        self.quality_combo = ttk.Combobox(main_frame, textvariable=self.quality_var, 
                                         values=["1080p", "720p", "480p", "360p", "240p"], 
                                         state="readonly", width=10)
        self.quality_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Audio Quality:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.audio_quality_var = tk.StringVar(value="128kbps")
        self.audio_combo = ttk.Combobox(main_frame, textvariable=self.audio_quality_var,
                                       values=["320kbps", "256kbps", "192kbps", "128kbps", "64kbps"],
                                       state="readonly", width=10)
        self.audio_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Output Directory:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(main_frame, textvariable=self.output_dir_var, width=40).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_directory).grid(row=4, column=2, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Get Video Info", command=self.get_video_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Download", command=self.start_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.info_text = scrolledtext.ScrolledText(main_frame, height=10, width=70)
        self.info_text.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)
        
        format_combo.bind('<<ComboboxSelected>>', self.on_format_change)
        
    def on_format_change(self, event=None):
        if self.format_var.get() == "mp3":
            self.quality_combo.config(state="disabled")
            self.audio_combo.config(state="readonly")
        else:
            self.quality_combo.config(state="readonly")
            self.audio_combo.config(state="disabled")
    
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
    
    def log_message(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.update()
    
    def clear_fields(self):
        self.url_var.set("")
        self.info_text.delete(1.0, tk.END)
        self.progress_var.set(0)
    
    def get_video_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        try:
            self.log_message("Fetching video information...")
            if "playlist" in url:
                playlist = Playlist(url)
                self.log_message(f"Playlist Title: {playlist.title}")
                self.log_message(f"Number of videos: {len(playlist.video_urls)}")
                self.log_message("\nVideos in playlist:")
                for video in playlist.videos:
                    self.log_message(f"- {video.title}")
            else:
                yt = YouTube(url)
                
                info = f"Title: {yt.title or 'Unknown'}\n"
                info += f"Author: {yt.author or 'Unknown'}\n"
                info += f"Length: {(yt.length // 60) if yt.length else 0}:{(yt.length % 60) if yt.length else 0:02d}\n"
                info += f"Views: {yt.views:,}\n" if yt.views else "Views: Unknown\n"
                
                try:
                    info += f"Rating: {yt.rating:.2f}\n\n" if yt.rating else "Rating: Unknown\n\n"
                except:
                    info += "Rating: Unknown\n\n"
                
                info += "Available Video Streams:\n"
                video_streams = yt.streams.filter(progressive=True, file_extension='mp4')
                if video_streams:
                    for stream in video_streams:
                        try:
                            size_mb = stream.filesize // 1024 // 1024 if stream.filesize else 0
                            info += f"  - {stream.resolution or 'Unknown'} MP4 ({size_mb} MB)\n"
                        except:
                            info += f"  - {stream.resolution or 'Unknown'} MP4 (Size unknown)\n"
                else:
                    info += "  - No progressive video streams available\n"
                
                info += "\nAvailable Audio Streams:\n"
                audio_streams = yt.streams.filter(only_audio=True)
                if audio_streams:
                    for stream in audio_streams:
                        try:
                            info += f"  - {stream.abr or 'Unknown'} {stream.mime_type or 'Unknown'}\n"
                        except:
                            info += f"  - Audio stream available\n"
                else:
                    info += "  - No audio streams available\n"
                
                self.log_message(info)
            
        except Exception as e:
            self.log_message(f"Error fetching video info: {str(e)}")
            messagebox.showerror("Error", f"Failed to get video info: {str(e)}")
    
    def sanitize_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.progress_var.set(percentage)
    
    def start_download(self):
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showwarning("Warning", "Download already in progress")
            return
        
        self.download_thread = threading.Thread(target=self.download_video_or_playlist)
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def download_video_or_playlist(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        if "playlist" in url:
            try:
                playlist = Playlist(url)
                self.log_message(f"Starting download for playlist: {playlist.title}")
                total_videos = len(playlist.video_urls)
                for i, video_url in enumerate(playlist.video_urls):
                    self.log_message(f"\n--- Downloading video {i+1} of {total_videos} ---")
                    self.download_single_video(video_url)
                messagebox.showinfo("Success", "Playlist download completed successfully!")
            except Exception as e:
                self.log_message(f"Playlist download failed: {str(e)}")
                messagebox.showerror("Error", f"Playlist download failed: {str(e)}")
        else:
            self.download_single_video(url)

    def download_single_video(self, url):
        try:
            self.progress_var.set(0)
            
            yt = YouTube(url, on_progress_callback=self.progress_callback)
            
            safe_title = self.sanitize_filename(yt.title or "Unknown_Video")
            output_dir = self.output_dir_var.get()
            
            if self.format_var.get() == "mp3":
                audio_stream = yt.streams.filter(only_audio=True).first()
                if not audio_stream:
                    raise Exception("No audio stream available")
                
                self.log_message(f"Downloading audio: {safe_title}")
                audio_file = audio_stream.download(output_path=output_dir, filename=f"{safe_title}.mp4")
                
                mp3_file = os.path.join(output_dir, f"{safe_title}.mp3")
                self.log_message("Converting to MP3...")
                
                try:
                    os.rename(audio_file, mp3_file)
                    self.log_message(f"Successfully downloaded: {mp3_file}")
                except:
                    self.log_message(f"Downloaded as MP4: {audio_file}")
                    
            else:
                quality = self.quality_var.get()
                
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality).first()
                
                if not video_stream:
                    video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    if video_stream:
                        actual_quality = video_stream.resolution or "Unknown"
                        self.log_message(f"Requested quality {quality} not available. Using {actual_quality}")
                
                if not video_stream:
                    raise Exception("No suitable video stream found")
                
                resolution = video_stream.resolution or "Unknown"
                self.log_message(f"Downloading video: {safe_title} ({resolution})")
                video_file = video_stream.download(output_path=output_dir, filename=f"{safe_title}.mp4")
                self.log_message(f"Successfully downloaded: {video_file}")
            
            self.progress_var.set(100)
            
        except Exception as e:
            self.log_message(f"Download failed for {url}: {str(e)}")
            self.progress_var.set(0)



class WebScraper:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.setup_ui()
        self.scrape_thread = None
        self.scraped_data = []
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Website URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Scrape Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.scrape_type_var = tk.StringVar(value="custom")
        scrape_combo = ttk.Combobox(main_frame, textvariable=self.scrape_type_var, 
                                   values=["custom", "links", "images", "text", "tables"], 
                                   state="readonly", width=15)
        scrape_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="CSS Selector:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.selector_var = tk.StringVar()
        selector_entry = ttk.Entry(main_frame, textvariable=self.selector_var, width=60)
        selector_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Delay (seconds):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.StringVar(value="1")
        delay_entry = ttk.Entry(main_frame, textvariable=self.delay_var, width=10)
        delay_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Output Directory:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(main_frame, textvariable=self.output_dir_var, width=40).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_directory).grid(row=4, column=2, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Preview", command=self.preview_scrape).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save CSV", command=self.save_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save JSON", command=self.save_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.results_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.results_text.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)
        
        scrape_combo.bind('<<ComboboxSelected>>', self.on_scrape_type_change)
        
    def on_scrape_type_change(self, event=None):
        scrape_type = self.scrape_type_var.get()
        if scrape_type == "links":
            self.selector_var.set("a")
        elif scrape_type == "images":
            self.selector_var.set("img")
        elif scrape_type == "text":
            self.selector_var.set("p, h1, h2, h3, h4, h5, h6")
        elif scrape_type == "tables":
            self.selector_var.set("table")
        else:
            self.selector_var.set("")
    
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
    
    def log_message(self, message):
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.update()
    
    def clear_fields(self):
        self.url_var.set("")
        self.selector_var.set("")
        self.results_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.scraped_data = []
    
    def get_page_content(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def preview_scrape(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL")
            return
        
        try:
            self.log_message("Fetching page content...")
            content = self.get_page_content(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            scrape_type = self.scrape_type_var.get()
            selector = self.selector_var.get().strip()
            
            if not selector and scrape_type == "custom":
                messagebox.showerror("Error", "Please enter a CSS selector for custom scraping")
                return
            
            elements = soup.select(selector)
            
            self.log_message(f"Found {len(elements)} elements matching '{selector}'")
            
            preview_count = min(5, len(elements))
            self.log_message(f"Preview (first {preview_count} items):")
            
            for i, element in enumerate(elements[:preview_count]):
                if scrape_type == "links":
                    href = element.get('href', '')
                    if href:
                        full_url = urljoin(url, href)
                        self.log_message(f"{i+1}. {element.text.strip()[:50]} -> {full_url}")
                elif scrape_type == "images":
                    src = element.get('src', '')
                    alt = element.get('alt', '')
                    if src:
                        full_url = urljoin(url, src)
                        self.log_message(f"{i+1}. {alt[:30]} -> {full_url}")
                else:
                    text = element.get_text().strip()
                    self.log_message(f"{i+1}. {text[:100]}...")
            
        except Exception as e:
            self.log_message(f"Preview failed: {str(e)}")
            messagebox.showerror("Error", f"Preview failed: {str(e)}")
    
    def start_scraping(self):
        if self.scrape_thread and self.scrape_thread.is_alive():
            messagebox.showwarning("Warning", "Scraping already in progress")
            return
        
        self.scrape_thread = threading.Thread(target=self.scrape_website)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def scrape_website(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL")
            return
        
        try:
            self.log_message("Starting web scraping...")
            self.progress_var.set(0)
            self.scraped_data = []
            
            delay = float(self.delay_var.get())
            
            content = self.get_page_content(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            scrape_type = self.scrape_type_var.get()
            selector = self.selector_var.get().strip()
            
            if not selector and scrape_type == "custom":
                messagebox.showerror("Error", "Please enter a CSS selector for custom scraping")
                return
            
            elements = soup.select(selector)
            total_elements = len(elements)
            
            self.log_message(f"Found {total_elements} elements to scrape")
            
            for i, element in enumerate(elements):
                if scrape_type == "links":
                    href = element.get('href', '')
                    if href:
                        full_url = urljoin(url, href)
                        data = {
                            'text': element.get_text().strip(),
                            'url': full_url,
                            'title': element.get('title', ''),
                            'index': i + 1
                        }
                        self.scraped_data.append(data)
                
                elif scrape_type == "images":
                    src = element.get('src', '')
                    if src:
                        full_url = urljoin(url, src)
                        data = {
                            'alt': element.get('alt', ''),
                            'src': full_url,
                            'title': element.get('title', ''),
                            'index': i + 1
                        }
                        self.scraped_data.append(data)
                
                elif scrape_type == "tables":
                    rows = element.find_all('tr')
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if cells:
                            data = {
                                'table_index': i + 1,
                                'row_index': row_idx + 1,
                                'cells': [cell.get_text().strip() for cell in cells]
                            }
                            self.scraped_data.append(data)
                
                else:
                    text = element.get_text().strip()
                    if text:
                        data = {
                            'text': text,
                            'tag': element.name,
                            'class': ' '.join(element.get('class', [])),
                            'id': element.get('id', ''),
                            'index': i + 1
                        }
                        self.scraped_data.append(data)
                
                progress = (i + 1) / total_elements * 100
                self.progress_var.set(progress)
                
                if delay > 0:
                    time.sleep(delay)
            
            self.log_message(f"Scraping completed! Extracted {len(self.scraped_data)} items")
            
            for item in self.scraped_data[:10]:
                if scrape_type == "links":
                    self.log_message(f"Link: {item['text'][:50]} -> {item['url']}")
                elif scrape_type == "images":
                    self.log_message(f"Image: {item['alt'][:30]} -> {item['src']}")
                elif scrape_type == "tables":
                    self.log_message(f"Table {item['table_index']}, Row {item['row_index']}: {', '.join(item['cells'][:3])}")
                else:
                    self.log_message(f"Text: {item['text'][:100]}...")
            
            if len(self.scraped_data) > 10:
                self.log_message(f"... and {len(self.scraped_data) - 10} more items")
            
            self.progress_var.set(100)
            messagebox.showinfo("Success", f"Scraping completed! Found {len(self.scraped_data)} items")
            
        except Exception as e:
            self.log_message(f"Scraping failed: {str(e)}")
            messagebox.showerror("Error", f"Scraping failed: {str(e)}")
            self.progress_var.set(0)
    
    def save_csv(self):
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to save. Please scrape a website first.")
            return
        
        try:
            output_dir = self.output_dir_var.get()
            filename = f"scraped_data_{int(time.time())}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if self.scraped_data:
                    fieldnames = self.scraped_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.scraped_data)
            
            self.log_message(f"Data saved to CSV: {filepath}")
            messagebox.showinfo("Success", f"Data saved to {filename}")
            
        except Exception as e:
            self.log_message(f"CSV save failed: {str(e)}")
            messagebox.showerror("Error", f"Failed to save CSV: {str(e)}")
    
    def save_json(self):
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to save. Please scrape a website first.")
            return
        
        try:
            output_dir = self.output_dir_var.get()
            filename = f"scraped_data_{int(time.time())}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.scraped_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.log_message(f"Data saved to JSON: {filepath}")
            messagebox.showinfo("Success", f"Data saved to {filename}")
            
        except Exception as e:
            self.log_message(f"JSON save failed: {str(e)}")
            messagebox.showerror("Error", f"Failed to save JSON: {str(e)}")


class PdfMergerModule:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.setup_ui()
        self.merge_thread = None

    def setup_ui(self):
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="PDF Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.folder_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2, pady=5)

        ttk.Label(main_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_name_var = tk.StringVar(value="merged.pdf")
        ttk.Entry(main_frame, textvariable=self.output_name_var, width=60).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Merge PDFs", command=self.start_merge).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.info_text = scrolledtext.ScrolledText(main_frame, height=10, width=70)
        self.info_text.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        main_frame.columnconfigure(1, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)

    def browse_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            self.folder_var.set(directory)

    def log_message(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.update()
    
    def clear_fields(self):
        self.folder_var.set("")
        self.info_text.delete(1.0, tk.END)
        self.progress_var.set(0)

    def start_merge(self):
        if self.merge_thread and self.merge_thread.is_alive():
            messagebox.showwarning("Warning", "Merge already in progress")
            return
        
        self.merge_thread = threading.Thread(target=self.merge_pdfs)
        self.merge_thread.daemon = True
        self.merge_thread.start()

    def merge_pdfs(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showerror("Error", "Please select a folder containing PDF files")
            return
        output_name = self.output_name_var.get().strip()
        if not output_name.endswith('.pdf'):
            output_name += '.pdf'
            return
        if not output_name:
            messagebox.showerror("Error", "Please enter a valid output file name")
            return
        
        try:
            self.log_message("Starting PDF merge...")
            self.progress_var.set(0)
            
            pdf_files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
            if not pdf_files:
                messagebox.showerror("Error", "No PDF files found in the selected folder")
                return
            
            merger = PdfMerger()
            total_files = len(pdf_files)
            
            for i, pdf_file in enumerate(pdf_files):
                pdf_path = os.path.join(folder, pdf_file)
                merger.append(pdf_path)
                
                progress = (i + 1) / total_files * 100
                self.progress_var.set(progress)
                self.log_message(f"Merged {pdf_file} ({i + 1}/{total_files})")
            
            output_path = os.path.join(folder, output_name)
            merger.write(output_path)
            merger.close()
            
            self.log_message(f"PDF merge completed! Output saved to: {output_path}")
            messagebox.showinfo("Success", f"PDF merge completed! Output saved to: {output_name}")

        except Exception as e:
            self.log_message(f"PDF merge failed: {str(e)}")
            messagebox.showerror("Error", f"Failed to merge PDFs: {str(e)}")
            self.progress_var.set(0)


class FileConverterModule:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.convert_thread = None
        self.conversion_options = {
            "Image": ["PNG", "JPG", "BMP", "GIF", "TIFF"],
            "Audio": ["MP3", "WAV", "OGG"],
            "Video": ["MP4", "WEBM", "MKV", "AVI"]
        }
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text='Input File:').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_file_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_file_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text='Browse', command=self.browse_input_file).grid(row=0, column=2, pady=5)

        ttk.Label(main_frame, text="Conversion Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.convert_type_var = tk.StringVar()
        self.convert_type_combo = ttk.Combobox(main_frame, textvariable=self.convert_type_var,
                                               values=list(self.conversion_options.keys()),
                                               state="readonly", width=15)
        self.convert_type_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.convert_type_combo.bind("<<ComboboxSelected>>", self.update_output_formats)

        ttk.Label(main_frame, text="Output Format:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_format_var = tk.StringVar()
        self.output_format_combo = ttk.Combobox(main_frame, textvariable=self.output_format_var,
                                                state="readonly", width=15)
        self.output_format_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Convert", command=self.start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        self.info_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.info_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        main_frame.columnconfigure(1, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)
    
    def browse_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("All files", "*.*"), ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                       ("Audio files", "*.mp3 *.wav *.ogg"), ("Video files", "*.mp4 *.webm *.mkv *.avi")]
        )
        if file_path:
            self.input_file_var.set(file_path)
    
    def update_output_formats(self, event=None):
        convert_type = self.convert_type_var.get()
        if convert_type in self.conversion_options:
            self.output_format_combo['values'] = self.conversion_options[convert_type]
            self.output_format_combo.set(self.conversion_options[convert_type][0])
        else:
            self.output_format_combo['values'] = []
            self.output_format_combo.set("")

    def log_message(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.update()
    
    def clear_fields(self):
        self.input_file_var.set("")
        self.convert_type_var.set("")
        self.output_format_var.set("")
        self.info_text.delete(1.0, tk.END)
        self.progress_var.set(0)
    
    def start_conversion(self):
        if self.convert_thread and self.convert_thread.is_alive():
            messagebox.showwarning("Warning", "Conversion already in progress")
            return
        
        self.convert_thread = threading.Thread(target=self.convert_file)
        self.convert_thread.daemon = True
        self.convert_thread.start()
    def convert_file(self):
        input_path = self.input_file_var.get()
        convert_type = self.convert_type_var.get()
        output_format = self.output_format_var.get().lower()
        if not all([input_path, convert_type, output_format]):
            messagebox.showerror("Error", "Please ensure to fill in all fields.")
            return
        try:
            self.progress_var.set(0)
            self.log_message(f"Starting conversion of {os.path.basename(input_path)} to {output_format.upper()}...")

            if convert_type == "Image":
                self.convert_image(input_path, output_format)
            elif convert_type in ["Audio", "Video"]:
                self.convert_media(input_path, output_format, convert_type)

            self.progress_var.set(100)
            self.log_message(f"Conversion completed successfully! Output saved to {os.path.splitext(input_path)[0]}.{output_format}")
            messagebox.showinfo("Yippee!", f"Conversion completed successfully! Output saved to {os.path.splitext(input_path)[0]}.{output_format}")

        except Exception as e:
            self.log_message(f"Conversion failed: {str(e)}")
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
        finally:
            self.progress_var.set(0)

    def convert_image(self, input_path, output_format):
        output_path = self.generate_output_path(input_path, output_format)
        img = Image.open(input_path)

        if output_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        img.save(output_path)
        self.log_message(f"Image converted and saved to {output_path}")
    def convert_media(self, input_path, output_format, media_type):
        output_path = self.generate_output_path(input_path, output_format)

        if media_type == 'Audio':
            clip = mp.AudioFileClip(input_path)
            clip.write_audiofile(output_path)
        elif media_type == 'Video':
            clip = mp.VideoFileClip(input_path)
            clip.write_videofile(output_path)

        self.log_message(f"{media_type} converted and saved to {output_path}.")

class BackgroundMusic:
    def __init__(self):
        pygame.mixer.init()
        self.is_playing = False
        self.current_file = None
        
    def play_music(self, file_path, loop=-1):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(loops=loop)
            self.is_playing = True
            self.current_file = file_path
            return True
        except Exception as e:
            print(f"Error playing music: {e}")
            return False
    
    def stop_music(self):
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def pause_music(self):
        pygame.mixer.music.pause()
        self.is_playing = False
    
    def resume_music(self):
        pygame.mixer.music.unpause()
        self.is_playing = True
    
    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)


class MultiFunctionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stevie's File Emporium")
        self.root.geometry("900x700")
        

        self.music = BackgroundMusic()
        

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        

        self.create_menu_bar()
        

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        self.youtube_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.youtube_frame, text="YouTube Converter")
        self.youtube_converter = YouTubeConverter(self.youtube_frame)
        

        self.scraper_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scraper_frame, text="Web Scraper")
        self.web_scraper = WebScraper(self.scraper_frame)
        

        self.pdf_merger_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pdf_merger_frame, text="PDF Merger")
        self.pdf_merger = PdfMergerModule(self.pdf_merger_frame)
        self.placeholder_frame2 = ttk.Frame(self.notebook)

        self.file_converter_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_converter_frame, text='File Converter')
        self.file_converter = FileConverterModule(self.file_converter_frame)
        
        

        self.auto_start_music()
        
    def auto_start_music(self):
        music_files = [
            "background_music.mp3",
            "bgm.mp3",
            "music.mp3",
            "background.wav",
            "bgm.wav",
            os.path.join(os.path.dirname(__file__), "background_music.mp3"),
            os.path.join(os.path.dirname(__file__), "bgm.mp3"),
            os.path.join(os.path.dirname(__file__), "music.mp3"),
            os.path.join(os.path.dirname(__file__), "background.wav"),
            os.path.join(os.path.dirname(__file__), "bgm.wav"),
        ]
        

        for music_file in music_files:
            if os.path.exists(music_file):
                if self.music.play_music(music_file, loop=-1):
                    self.status_var.set(f"Auto-playing: {os.path.basename(music_file)}")
                    return

        self.status_var.set("No background music found - place 'background_music.mp3' in program directory")
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        music_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Music", menu=music_menu)
        music_menu.add_command(label="Load New Music", command=self.load_music)
        music_menu.add_separator()
        music_menu.add_command(label="Play", command=self.play_music)
        music_menu.add_command(label="Pause", command=self.pause_music)
        music_menu.add_command(label="Stop", command=self.stop_music)
        music_menu.add_separator()
        music_menu.add_command(label="Volume", command=self.set_volume)
        music_menu.add_separator()
        music_menu.add_command(label="Restart Auto Music", command=self.auto_start_music)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def load_music(self):
        file_path = filedialog.askopenfilename(
            title="Select Music File",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")]
        )
        if file_path:
            self.music.stop_music()
            if self.music.play_music(file_path, loop=-1):
                self.status_var.set(f"Now playing: {os.path.basename(file_path)}")
            else:
                self.status_var.set("Failed to play selected music file")
    
    def play_music(self):
        if self.music.is_playing:
            self.status_var.set("Music is already playing")
        else:
            if self.music.current_file:
                if self.music.play_music(self.music.current_file, loop=-1):
                    self.status_var.set("Music resumed")
                else:
                    self.status_var.set("Failed to resume music")
            else:
                self.auto_start_music()
    
    def pause_music(self):
        self.music.pause_music()
        self.status_var.set("Music paused")
    
    def stop_music(self):
        self.music.stop_music()
        self.status_var.set("Music stopped")
    
    def set_volume(self):
        volume_window = tk.Toplevel(self.root)
        volume_window.title("Volume Control")
        volume_window.geometry("300x100")
        
        volume_var = tk.DoubleVar(value=50)
        ttk.Label(volume_window, text="Volume:").pack(pady=5)
        volume_scale = ttk.Scale(volume_window, from_=0, to=100, variable=volume_var, orient=tk.HORIZONTAL)
        volume_scale.pack(fill=tk.X, padx=20, pady=5)
        
        def apply_volume():
            self.music.set_volume(volume_var.get() / 100)
            volume_window.destroy()
        
        ttk.Button(volume_window, text="Apply", command=apply_volume).pack(pady=10)
    
    def show_about(self):
        about_text = """Welcome to Stevie's File Emporium!
        \nThis application is basically a collection of tools for things I use on the daily, and want to avoid the conversion sites with the dodgy ads.
        \nPretty happy with its current state but ill surely add more when inspiration strikes me.
        \nI hope you enjoy what I've put together, this took like 10 hours so yeah I hope it was worth smile emoji
        \nOh and also feel free to request features or report bugs, my contact is below!
        \n\nCreated by Stevie Dandy.
        \nContact: stephen.dandy@hotmail.com"""
        
        messagebox.showinfo("About", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = MultiFunctionApp(root)
    root.mainloop()