import os
import platform
import shutil
import subprocess
import sys
import re

def get_audio_bitrate(file_path):
    """
    Uses ffprobe to get the bitrate of an audio file in kbps.
    Returns float (kbps) or None if failed.
    """
    ffmpeg_dir = get_ffmpeg_path()
    ffprobe_cmd = "ffprobe"
    if ffmpeg_dir:
        ffprobe_cmd = os.path.join(ffmpeg_dir, "ffprobe.exe" if platform.system() == "Windows" else "ffprobe")
    
    cmd = [
        ffprobe_cmd, 
        "-v", "error", 
        "-show_entries", "format=bit_rate", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    
    try:
        # If ffprobe isn't found, this might fail unless in PATH
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            # Output is in bits/s, e.g. "128000"
            bps = float(result.stdout.strip())
            return bps / 1000.0
    except Exception:
        pass
        
    return None

def get_ffmpeg_path():
    """
    Intelligently attempts to find the FFmpeg directory.
    Checks in order:
    1. System PATH (returns None, letting system handle it)
    2. 'bin' folder in current directory (portable mode)
    3. Common Windows Winget paths (fallback)
    Returns: Directory path containing ffmpeg.exe, or None if relying on system PATH.
    """
    # 1. Check local 'bin' folder
    local_bin = os.path.join(os.getcwd(), 'bin')
    if os.path.exists(os.path.join(local_bin, 'ffmpeg.exe')):
        return local_bin

    # 2. Check specific Windows paths (legacy/Winget support)
    if platform.system() == "Windows":
        winget_path = r"C:\Users\michi\AppData\Local\Microsoft\Winget\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
        if os.path.exists(os.path.join(winget_path, 'ffmpeg.exe')):
            return winget_path
            
    # 3. Check if globally available via PATH
    if shutil.which("ffmpeg"):
        return None # Already in PATH
            
    return None

def update_yt_dlp():
    """
    Updates the yt-dlp package using pip.
    Returns (success: bool, message: str)
    """
    try:
        print("Updating yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
        return True, "yt-dlp updated successfully!"
    except Exception as e:
        return False, f"Error: {e}"

def get_enhancement_filters(is_low_quality=False, preset="Smart (Auto)", output_format="flac"):
    """
    Returns a list of FFmpeg filter strings for the "Smart Remaster" engine v2.0.
    Supports Presets: 'Smart (Auto)', 'Bass Boost', 'Vocal Clarity', 'Dynamic'.
    """
    filters = []
    
    # Preset Definitions (Base Curves)
    # --------------------------------
    base_eq = []
    
    if preset == "Bass Boost (Club)":
        # Focus: Deep Lows (40-80Hz) + Punchy Kicks (100Hz)
        # Recess mids slightly to make room for bass.
        base_eq.append("equalizer=f=50:width_type=o:width=1.5:g=5")    # Sub-bass
        base_eq.append("equalizer=f=100:width_type=o:width=1.0:g=3")   # Kick
        base_eq.append("equalizer=f=400:width_type=o:width=1.0:g=-2")  # Mud cut
        
    elif preset == "Vocal Clarity":
        # Focus: Dialogue and Vocals (1kHz - 4kHz)
        # Cut lows significantly to reduce rumble.
        base_eq.append("highpass=f=90")
        base_eq.append("equalizer=f=1500:width_type=o:width=1.5:g=3")  # Presence
        base_eq.append("equalizer=f=3500:width_type=o:width=1.0:g=2")  # Intelligibility
        
    elif preset == "Dynamic (Pop/Rock)":
        # Focus: Snare snap and Guitar bite. V-Shape.
        base_eq.append("equalizer=f=80:width_type=o:width=1.0:g=3")    # Body
        base_eq.append("equalizer=f=2500:width_type=o:width=2.0:g=2")  # Edge
        base_eq.append("equalizer=f=8000:width_type=h:width=2000:g=3") # Highs
        
    elif preset == "Studio Hi-Res (Upscale)":
        base_eq.append("equalizer=f=30:width_type=o:width=2.0:g=2")
        base_eq.append("equalizer=f=12000:width_type=h:width=2000:g=3")

    # "Smart (Auto)" uses the dynamic multi-band logic below as its core, so no static EQ needed yet.

    # --- STAGE 1: MULTI-BAND DYNAMICS (The Engine) ---
    # We tweak the crossover compression based on preset.
    
    if preset == "Vocal Clarity":
        # Less bass compression, more mid-range leveling
        mcompand_str = (
            "mcompand="
            "0.005,0.1 6 -40,-20,-10 " # Lows: Reduce dynamically
            "200 " 
            "0.002,0.05 6 -20,-8,-1 "  # Mids: Aggressive leveling for vocals
            "5000 "
            "0.002,0.05 6 -24,-12,-3"  # Highs: Soft
        )
    elif preset == "Studio Hi-Res (Upscale)":
        mcompand_str = (
            "mcompand="
            "0.005,0.1 6 -40,-20,-3 " 
            "120 " 
            "0.005,0.05 6 -30,-10,-2 " 
            "5000 "
            "0.005,0.05 6 -30,-10,-1"
        )
    else:
        # Default "Modern Punchy" Compand (Used for Smart, Bass Boost, Dynamic)
        mcompand_str = (
            "mcompand="
            "0.005,0.1 6 -24,-12,-6 " # Lows
            "120 "                    
            "0.003,0.05 6 -20,-8,-3 " # Mids
            "6000 "                   
            "0.002,0.05 6 -18,-9,-1"  # Highs
        )
    
    filters.append(mcompand_str)
    filters.extend(base_eq) # Apply static EQ after dynamics

    # --- STAGE 2: RESTORATION (Low Quality Handling) ---
    if is_low_quality:
        filters.append("crystalizer=i=3.5") 
        filters.append("equalizer=f=12000:width_type=h:width=2000:g=4") # Fake Highs
    else:
        # Hi-Fi Polish
        filters.append("crystalizer=i=1.5")
        if preset == "Studio Hi-Res (Upscale)":
             filters.append("crystalizer=i=2.5")
             filters.append("highshelf=f=10000:g=4")
        elif preset != "Vocal Clarity":
             # Don't boost air too much on vocals to avoid sibilance
             filters.append("equalizer=f=16000:width_type=h:width=1000:g=3")

    # --- STAGE 3: STEREO IMAGE ---
    # Wider for Club/Smart, Narrower for Vocal
    width = 1.0
    if preset in ["Smart (Auto)", "Bass Boost (Club)"]: width = 1.25
    elif preset == "Dynamic (Pop/Rock)": width = 1.15
    elif preset == "Studio Hi-Res (Upscale)": width = 1.10
    
    filters.append(f"stereotools=mlev=1:slev={width}")

    # --- STAGE 4: CLEANUP & LIMITER ---
    filters.append("alimiter=limit=-1dB:level_in=1:level_out=1:attack=5:release=50")
    if preset == "Studio Hi-Res (Upscale)":
        # Target higher LUFS or leave dynamics more intact? Let's fix at standard
        filters.append("loudnorm=I=-14:TP=-1.0:LRA=11")
        filters.append("silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:detection=peak")
        if output_format == "flac":
            filters.append("aresample=resampler=soxr:precision=28")
            filters.append("aformat=sample_rates=96000:sample_fmts=s32")
        else:
            filters.append("aformat=sample_rates=48000")
    else:
        filters.append("loudnorm=I=-14:TP=-1.0:LRA=11")
        filters.append("silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:detection=peak")
        filters.append("aformat=sample_rates=48000")
    
    return filters

def convert_audio(input_path, output_format):
    """
    Converts audio to target format using FFmpeg.
    Returns (success: bool, message: str, output_path: str)
    """
    try:
        ffmpeg_dir = get_ffmpeg_path()
        ffmpeg_cmd = "ffmpeg"
        if ffmpeg_dir:
            ffmpeg_cmd = os.path.join(ffmpeg_dir, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")

        # Determine output filename
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_converted.{output_format}"
        
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", input_path,
            "-map", "0:a", # Map audio only
        ]
        
        # Codec selection
        if output_format == 'mp3':
            cmd.extend(["-c:a", "libmp3lame", "-b:a", "320k"])
        elif output_format == 'flac':
             cmd.extend(["-c:a", "flac"])
        elif output_format == 'm4a':
             cmd.extend(["-c:a", "aac", "-b:a", "256k"])
             
        cmd.append(output_path)
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, "Conversion successful!", output_path
        
    except Exception as e:
        return False, f"Conversion failed: {str(e)}", None

def write_metadata(file_path, title=None, artist=None, album=None):
    """
    Updates metadata for an audio file.
    Returns (success: bool, message: str)
    """
    try:
        ffmpeg_dir = get_ffmpeg_path()
        ffmpeg_cmd = "ffmpeg"
        if ffmpeg_dir:
            ffmpeg_cmd = os.path.join(ffmpeg_dir, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
            
        # We need a temp file because ffmpeg can't edit in place easily without re-encoding complexity in some containers
        # But for metadata 'copy' is fast.
        temp_path = file_path + ".tmp" + os.path.splitext(file_path)[1]
        
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", file_path,
            "-map", "0", 
            "-c", "copy",
        ]
        
        if title: cmd.extend(["-metadata", f"title={title}"])
        if artist: cmd.extend(["-metadata", f"artist={artist}"])
        if album: cmd.extend(["-metadata", f"album={album}"])
        
        cmd.append(temp_path)
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # If successful, replace original
        os.replace(temp_path, file_path)
        return True, "Metadata saved!"
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, f"Error saving tags: {str(e)}"

def search_youtube(query, limit=10):
    """
    Searches YouTube for the query using yt-dlp.
    Returns a list of dicts: {title, url, duration, thumbnail, uploader}
    """
    try:
        # We process here using the library directly if available.
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'extract_flat': True, # Fast extraction
            'noplaylist': True,
            'limit': limit,
        }
        
        results = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    results.append({
                        'title': entry.get('title'),
                        'url': entry.get('url'), # usually just ID in flat mode
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader'),
                        'thumbnail': entry.get('thumbnails', [{}])[0].get('url') if entry.get('thumbnails') else None
                    })
        return results

    except Exception as e:
        print(f"Search error: {e}")
        return []
