import yt_dlp
import os
import sys
from utils import get_ffmpeg_path, get_enhancement_filters

def download_music(url, status_hook=None, audio_format='mp3', preset="Smart (Auto)"):
    def progress_hook(d):
        if status_hook:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').replace('%','')
                try:
                    status_hook(f"Downloading: {d['_percent_str']}", float(percent)/100)
                except:
                    pass
            elif d['status'] == 'finished':
                status_hook("Processing audio...", 1.0)

    # Configure Extraction Options (No Download)
    extract_opts = {
        'quiet': True,
        'noplaylist': False, # We handle playlists by iterating
        'extract_flat': 'in_playlist', # fast extraction for playlists
        'extractor_args': {'youtube': {'player_client': ['android']}}, # Bypasses Render/Datacenter API blocks
    }
    
    if os.path.exists("youtube_cookies.txt"):
        extract_opts['cookiefile'] = "youtube_cookies.txt"

    # Set FFmpeg location for extraction too (if needed for some probes, though mostly ytdlp handles it)
    ffmpeg_bin = get_ffmpeg_path()
    
    try:
        # Pre-analyze to detect quality (bitrate)
        if status_hook: status_hook("Analyzing metadata...", 0.1)
        
        # We need a fresh ydl object for extraction
        with yt_dlp.YoutubeDL(extract_opts) as ydl_extract:
            info = ydl_extract.extract_info(url, download=False)

        # Handle Playlist vs Single Video
        if 'entries' in info:
            entries = info['entries']
            print(f"Playlist detected: {len(entries)} items")
        else:
            entries = [info]

        # Prepare main download options blueprint
        base_ydl_opts = {
            'format': 'bestaudio/best',
            'progress_hooks': [progress_hook],
            'sponsorblock_remove': ['music_offtopic', 'intro', 'outro', 'selfpromo', 'preview', 'interaction'],
            'writethumbnail': True,
            'outtmpl': 'downloads/%(artist)s - %(title)s.%(ext)s',
            'noplaylist': True, # We handle iteration manually now
            'extractor_args': {'youtube': {'player_client': ['android']}}, # Bypasses Render/Datacenter API blocks
        }
        if ffmpeg_bin:
            base_ydl_opts['ffmpeg_location'] = ffmpeg_bin

        # Iterate and Download
        downloaded_items = []
        
        for i, entry in enumerate(entries):
            video_url = entry.get('url') or entry.get('webpage_url') or url # Fallback
            title = entry.get('title', 'Unknown')
            artist = entry.get('artist', 'Unknown Artist')
            
            # 1. Analyze Quality
            # yt-dlp 'abr' is average bitrate in kbps. If missing, assume good quality (safe default).
            abr = entry.get('abr')
            if abr is None:
                # Try to guess from formats if available, otherwise assume HQ
                formats = entry.get('formats', [])
                if formats:
                    # simplistic max abr check
                    abr = max([f.get('abr', 0) for f in formats if f.get('abr')]) or 192
                else:
                    abr = 192 # Default assumption
            
            is_low_quality = abr < 128
            quality_tag = " [Low Quality]" if is_low_quality else ""
            print(f"Processing: {title} ({int(abr)}kbps){quality_tag}")
            
            msg = f"Downloading: {title}..."
            if is_low_quality:
                msg = f"Enhancing ({int(abr)}kbps): {title}..."
            
            if status_hook: status_hook(msg, 0.1)

            # 2. Get Filters based on analysis and preset
            filters = get_enhancement_filters(is_low_quality=is_low_quality, preset=preset, output_format=audio_format)
            if is_low_quality:
                print("  -> Applying Smart Enhancement (Crystalizer + EQ)")
            full_filter_str = ",".join(filters)
            
            # 3. Setup Postprocessors
            pp_args = ['-af', full_filter_str]
            
            if audio_format == 'flac':
                preferred_codec = 'flac'
                preferred_quality = None
                ext = 'flac'
            else:
                preferred_codec = 'mp3'
                preferred_quality = '320'
                ext = 'mp3'
                pp_args.extend(['-id3v2_version', '3'])

            current_opts = base_ydl_opts.copy()
            current_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': preferred_codec,
                    'preferredquality': preferred_quality,
                },
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata', 'add_metadata': True}
            ]
            current_opts['postprocessor_args'] = {'FFmpegExtractAudio': pp_args}

            # 4. Download Single Item
            with yt_dlp.YoutubeDL(current_opts) as ydl:
                # If we have a direct video ID/URL from extract_info
                # We can pass the original URL but restrict to the specific video if it was a playlist
                # BUT 'extract_flat' gives minimal info. 
                # Better: Re-use the URL if single, or entry ID if playlist.
                target = entry.get('webpage_url', url)
                info_processed = ydl.extract_info(target, download=True)
                
                # Get final filename? 
                # yt-dlp 'prepare_filename' might differ post-processing.
                # Simplest is to assume standard naming or list dir, but let's try to construct it or pass it.
                # Actually, simply returning metadata is good enough for now, 
                # let's try to capture the filename from info_processed 'requested_downloads' if available or 'filename'
                
                final_path = ydl.prepare_filename(info_processed)
                # Correct extension
                final_path = os.path.splitext(final_path)[0] + f".{ext}"
                
                downloaded_items.append({
                    "title": title,
                    "artist": artist,
                    "file_path": os.path.abspath(final_path),
                    "format": ext
                })
                
        print("\n[SUCCESS] All downloads complete!")
        if status_hook: status_hook("Ready", 1.0)
        
        return downloaded_items
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        if status_hook: status_hook(f"Error: {e}", 0.0)
        return []

if __name__ == "__main__":
    print("--- MusicPro Downloader (Smart Enhance) ---")
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        download_music(url)
    else:
        while True:
            url = input("\nEnter YouTube URL (Video or Playlist): ").strip()
            
            if url:
                print("\nChoose Format:")
                print("1. MP3 (320kbps)")
                print("2. FLAC (Lossless)")
                fmt_choice = input("Select format (1/2) [default: 1]: ").strip()
                
                audio_fmt = 'flac' if fmt_choice == '2' else 'mp3'
                
                print("\nSound Profiles:")
                print("1. Smart (Auto) [Balanced]")
                print("2. Bass Boost (Club)")
                print("3. Vocal Clarity")
                print("4. Dynamic (Pop/Rock)")
                
                profile_map = {"1": "Smart (Auto)", "2": "Bass Boost (Club)", "3": "Vocal Clarity", "4": "Dynamic (Pop/Rock)"}
                p_choice = input("Select Profile (1-4) [default: 1]: ").strip()
                preset = profile_map.get(p_choice, "Smart (Auto)")
                
                download_music(url, audio_format=audio_fmt, preset=preset)
            else:
                print("Invalid URL.")
            
            choice = input("\nDo you want to download another? (y/n): ").strip().lower()
            if choice != 'y':
                print("Goodbye!")
                break
