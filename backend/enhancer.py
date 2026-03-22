import os
import subprocess
import platform
import shutil
from utils import get_ffmpeg_path, get_enhancement_filters

# Configuration
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.flac', '.ogg')

def enhance_audio(input_path, output_path, is_low_quality=False, preset="Smart (Auto)"):
    print(f"Processing: {os.path.basename(input_path)}...")
    
    # Determine format based on output extension
    is_flac = output_path.lower().endswith('.flac')
    
    # Construct Filter Chain
    filters = get_enhancement_filters(is_low_quality=is_low_quality, preset=preset, output_format="flac" if is_flac else "mp3")
    
    full_filter_str = ",".join(filters)

    # Get FFmpeg binary logic
    ffmpeg_dir = get_ffmpeg_path()
    if ffmpeg_dir:
        ffmpeg_cmd = os.path.join(ffmpeg_dir, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
    else:
        ffmpeg_cmd = "ffmpeg" # Fallback to system path

    command = [
        ffmpeg_cmd,
        '-y', # Overwrite output
        '-i', input_path,
        '-af', full_filter_str,
    ]
    
    if is_flac:
        # FLAC is lossless
        pass 
    else:
        # For MP3/others, force high quality MP3
        command.extend(['-b:a', '320k', '-id3v2_version', '3'])

    command.append(output_path)
    
    try:
        # Run FFmpeg
        subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print("  [OK] Enhanced")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed: {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        return False

def main():
    print("--- MusicPro Audio Enhancer (Smart Remaster Engine v2.0) ---")
    print("This tool uses Multi-Band Compression to restore dynamics and clarity.")
    print("It will process your ENTIRE folder automatically.")
    
    folder_path = input("\nEnter the folder path containing your music: ").strip().strip('"')
    
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        input("Press Enter to exit...")
        return

    # Ask for Sound Profile
    print("\nSound Profiles:")
    print("1. Smart (Auto) [Balanced]")
    print("2. Bass Boost (Club)")
    print("3. Vocal Clarity")
    print("4. Dynamic (Pop/Rock)")
    
    profile_map = {"1": "Smart (Auto)", "2": "Bass Boost (Club)", "3": "Vocal Clarity", "4": "Dynamic (Pop/Rock)"}
    p_choice = input("Select Profile (1-4) [default: 1]: ").strip()
    preset = profile_map.get(p_choice, "Smart (Auto)")
    
    print(f"\nSelected Profile: {preset}")

    # Create output folder
    output_folder = os.path.join(folder_path, "enhanced")
    os.makedirs(output_folder, exist_ok=True)
    
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED_EXTENSIONS)]
    
    if not files:
        print("No music files found in this folder.")
        input("Press Enter to exit...")
        return
        
    print(f"\nFound {len(files)} files. Starting enhancement...\n")
    
    success_count = 0
    for filename in files:
        input_file = os.path.join(folder_path, filename)
        output_file = os.path.join(output_folder, filename)
        
        # 1. Analyze File Quality
        from utils import get_audio_bitrate # Lazy import to avoid circular if top-level messed up
        bitrate = get_audio_bitrate(input_file)
        
        # Default to standard if unknown, or if < 128k treat as low quality
        is_low_quality = False
        bitrate_str = "?"
        
        if bitrate:
            bitrate_str = f"{int(bitrate)}kbps"
            if bitrate < 128:
                is_low_quality = True
        
        tag = " [Smart Restore]" if is_low_quality else ""
        print(f"File: {filename} ({bitrate_str}){tag}")
        
        if enhance_audio(input_file, output_file, is_low_quality=is_low_quality, preset=preset):
            success_count += 1
            
    print(f"\nDone! {success_count}/{len(files)} files processed.")
    print(f"Enhanced files are in: {output_folder}")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
