# Stevie's File Emporium

Welcome to my file emporium! It's a bunch of tools I threw together in Python with a Tkinter GUI. It's a bit barebones, but it does some pretty useful stuff. Took me a fair few hours to get it all working, so I hope people may find some use from it.

---

## What's in the box?

Basically, it's a multi-tool for downloading and managing files. It's got a few different tabs for different jobs:

### YouTube Converter
This is probably the main reason I made this thing. You can chuck in a YouTube URL and get stuff from it.
- **Download Videos:** Grab videos as MP4 files. You can even pick the quality, but if that quality isn't there it'll just get the best one it can find.
- **Download Audio:** Rip the audio directly to an MP3.
- **Playlist Support:** This also can download whole playlists, without the dumb limits that websites have.

### Web Scraper
I added a web scraper, I don't know how useful it is to most people but it works. I like to use it to take images from a webpage, or mass acquiring links from indeed and stuff.
- **Scrape by Type:** Has presets to grab all the links, images, text, or tables from a URL.
- **Custom CSS Selectors:** You can use your own CSS selectors to get exactly what you want. I personally would recommend using the presets however.
- **Save Your Stuff:** You can save the data you've scraped as a CSV or JSON file.

### PDF Merger
This one's pretty simple. Got a folder full of PDFs you need to stick together? Use this to do that!
- **Select a Folder**
- **Numerical Sorting:** It's smart enough to sort the files by number (e.g., `1.pdf`, `2.pdf`, `10.pdf`) so they merge in the right order.
- **Merge!:** It'll produce a single `merged.pdf` file in that same folder. You can rename this merged file too if you so wish.

### File Converter
Pretty self explantory...
- **Images:** Convert between common image formats like PNG, JPG, BMP, etc.
- **Audio/Video:** Convert between major audio and video formats like MP3, WAV, MP4, AVI, etc.

## Dependencies
There are a fair few dependencies, but they should all install automatically when you run the script. You are of course welcome to check which libraries this project uses by checking the code yourself!
