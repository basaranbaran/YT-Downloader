from flask import Flask, render_template, request, jsonify, Response, send_file, stream_with_context
import yt_dlp
import os
import re
import uuid
import threading

app = Flask(__name__)

# Global dictionary to track active downloads for cancellation
active_downloads = {}
download_lock = threading.Lock()

# Common headers to avoid 403 Forbidden
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def config():
    download_path = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    return jsonify({'download_path': download_path})

@app.route('/api/cancel', methods=['POST'])
def cancel_download():
    data = request.json
    download_id = data.get('download_id')
    
    if not download_id:
        return jsonify({'error': 'download_id is required'}), 400
    
    with download_lock:
        if download_id in active_downloads:
            active_downloads[download_id]['cancelled'] = True
            return jsonify({'status': 'cancelled', 'message': 'Download cancellation requested'})
        else:
            return jsonify({'error': 'Download not found'}), 404

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': HTTP_HEADERS,
            'nocheckcertificate': True,
            'extract_flat': 'in_playlist', # Extract playlist info quickly without downloading
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            is_playlist = False
            if 'entries' in info:
                is_playlist = True
                # Just get the first video or generic info if possible for display
                # Or just basic playlist info
                title = info.get('title', 'Playlist')
                # Thumbnails might be in entries
                thumbnail = None
                if info.get('thumbnails'):
                    thumbnail = info['thumbnails'][-1]['url']
                elif info.get('entries') and len(info['entries']) > 0:
                     first_entry = info['entries'][0]
                     thumbnail = first_entry.get('thumbnails', [{}])[-1].get('url')
                
                # Resolutins might vary per video, so we offer generic "Best" or standard for playlists
                resolutions = ['1080p', '720p', '480p'] 
                formatted_resolutions = resolutions
            else:
                title = info.get('title')
                thumbnail = info.get('thumbnail')
                
                formats = info.get('formats', [])
                resolutions = set()
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('height'):
                        resolutions.add(f['height'])
                
                sorted_resolutions = sorted(list(resolutions), reverse=True)
                formatted_resolutions = [f"{res}p" for res in sorted_resolutions]

            # Get additional info for single videos
            uploader = None
            duration = None
            if not is_playlist:
                uploader = info.get('uploader', 'Unknown')
                duration_seconds = info.get('duration')
                if duration_seconds:
                    minutes = duration_seconds // 60
                    seconds = duration_seconds % 60
                    duration = f"{minutes}:{seconds:02d}"
            
            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'is_playlist': is_playlist,
                'playlist_count': len(info.get('entries', [])) if is_playlist else 0,
                'resolutions': formatted_resolutions,
                'uploader': uploader,
                'duration': duration
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    file_type = data.get('type') # 'video' or 'audio'
    quality = data.get('quality') # 'best', '1080', '720', etc.
    download_mode = data.get('mode', 'single') # 'single' or 'playlist'

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    download_folder_base = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(download_folder_base):
        os.makedirs(download_folder_base)

    # Base options
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'logtostderr': True,
        'http_headers': HTTP_HEADERS,
        'nocheckcertificate': True,
    }

    try:
        # Check if it is a playlist request
        if download_mode == 'playlist':
             # Generate unique download ID for cancellation
             download_id = str(uuid.uuid4())
             
             def generate_playlist_download():
                 try:
                     # Register this download
                     with download_lock:
                         active_downloads[download_id] = {'cancelled': False}
                     
                     # Get playlist info
                     # Yield status with padding to flush buffers (2048 spaces)
                     yield f"data: {{'status': 'info', 'message': 'Fetching playlist info...', 'download_id': '{download_id}'}}\n\n" + " " * 2048 + "\n\n"
                     
                     # Check for cancellation
                     with download_lock:
                         if active_downloads.get(download_id, {}).get('cancelled', False):
                             yield f"data: {{'status': 'cancelled', 'message': 'Download cancelled by user'}}\n\n"
                             return
                     
                     with yt_dlp.YoutubeDL({'quiet':True, 'extract_flat': 'in_playlist'}) as ydl:
                         pl_info = ydl.extract_info(url, download=False)
                         pl_title = pl_info.get('title', 'Unknown Album')
                         safe_pl_title = re.sub(r'[\\/*?:"<>|]', "", pl_title)
                     
                     album_folder = os.path.join(download_folder_base, safe_pl_title)
                     if not os.path.exists(album_folder):
                         os.makedirs(album_folder)

                     entries = pl_info.get('entries', [])
                     total = len(entries)
                     yield f"data: {{'status': 'info', 'message': 'Found {total} tracks in {pl_title}'}}\n\n"
                     
                     count = 0
                     for i, entry in enumerate(entries):
                         # Check for cancellation before each track
                         with download_lock:
                             if active_downloads.get(download_id, {}).get('cancelled', False):
                                 yield f"data: {{'status': 'cancelled', 'message': 'Download cancelled by user'}}\n\n"
                                 return
                         
                         try:
                             video_url = entry.get('url') 
                             if not video_url: 
                                 video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                             
                             track_title = entry.get('title', f'Track {i+1}')
                             yield f"data: {{'status': 'progress', 'current': {i+1}, 'total': {total}, 'message': 'Downloading: {track_title}'}}\n\n"
                             
                             # Reuse the single download logic helper
                             try:
                                 process_single_download(video_url, file_type, quality, album_folder)
                                 count += 1
                             except Exception as e:
                                 raise e
                             yield f"data: {{'status': 'success', 'message': 'Completed: {track_title}'}}\n\n"
                         except Exception as track_error:
                             print(f"Error downloading track {i}: {track_error}")
                             yield f"data: {{'status': 'error', 'message': 'Failed: {track_title} - {str(track_error)}'}}\n\n"

                     yield f"data: {{'status': 'done', 'message': 'All downloads completed at {album_folder}'}}\n\n"
                     
                 except Exception as e:
                     yield f"data: {{'status': 'error', 'message': 'Playlist Error: {str(e)}'}}\n\n"
                 finally:
                     # Clean up download tracking
                     with download_lock:
                         if download_id in active_downloads:
                             del active_downloads[download_id]
            
             return Response(stream_with_context(generate_playlist_download()), mimetype='text/event-stream')
             
        else:
            # Single Video Download
            # If URL contains playlist parameter, remove it to get single video
            # This ensures we get the video title, not playlist title
            single_video_url = url
            if 'list=' in url or '&index=' in url:
                # Remove playlist parameters to get single video
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                # Keep only video ID, remove list and index
                if 'v' in params:
                    single_video_url = f"https://www.youtube.com/watch?v={params['v'][0]}"
            
            filepath = process_single_download(single_video_url, file_type, quality, download_folder_base)
            return send_file(filepath, as_attachment=True)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def process_single_download(url, file_type, quality, target_folder):
    download_id = str(uuid.uuid4())
    
    # Create hidden temp folder
    temp_folder = os.path.join(os.getcwd(), 'downloads', '.temp')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Base options reused
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'logtostderr': True,
        'http_headers': HTTP_HEADERS,
        'nocheckcertificate': True,
        'noplaylist': True,  # Always extract single video, ignore playlist
    }

    if file_type == 'audio':
        # Simple Audio Download (MP3)
        # For audio, we download directly to target as it is usually a single file operation
        # But if post-processing is involved, yt-dlp might create temps.
        # Let's keep audio simple as it usually doesn't create multiple visible chunks like video merge.
        # OR we can download to temp and move. Let's download to temp and move to be safe.
        
        output_template = os.path.join(temp_folder, f'%(title)s_{download_id}.%(ext)s')
        ydl_opts = common_opts.copy()
        ydl_opts.update({
            'outtmpl': output_template,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            temp = ydl.prepare_filename(info)
            temp_mp3 = os.path.splitext(temp)[0] + '.mp3'
            
            # If temp_mp3 doesn't exist, try to find the actual downloaded file
            if not os.path.exists(temp_mp3):
                # Look for any file with the download_id in temp folder
                for file in os.listdir(temp_folder):
                    if download_id in file and file.endswith('.mp3'):
                        temp_mp3 = os.path.join(temp_folder, file)
                        break
                else:
                    raise Exception("Could not find downloaded audio file")
            
            # Clean title for filename
            clean_title = re.sub(r'[\\/*?:"<>|]', "", info['title'])
            final_filename = os.path.join(target_folder, f"{clean_title}.mp3")
            
            if os.path.exists(final_filename):
                 try: os.remove(final_filename)
                 except: pass
            
            os.rename(temp_mp3, final_filename)
            return final_filename

    else:
        # Optimized Video Download - Let yt-dlp handle merging automatically
        # This is faster than manual video+audio download + ffmpeg merge
        # Build format selector - yt-dlp will auto-merge video+audio
        if quality and quality != 'best':
            # Prefer MP4 container with H264 video and AAC audio at target quality
            vid_format = f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
        else:
            # Best quality with MP4 preference
            vid_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
        
        output_template = os.path.join(temp_folder, f'%(title)s_{download_id}.%(ext)s')
        ydl_opts = common_opts.copy()
        ydl_opts.update({
            'format': vid_format,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',  # Force MP4 output when merging
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual filename that was created
            temp_file = ydl.prepare_filename(info)
            # yt-dlp might add .mp4 extension after merge
            if not temp_file.endswith('.mp4'):
                temp_file_mp4 = os.path.splitext(temp_file)[0] + '.mp4'
                if os.path.exists(temp_file_mp4):
                    temp_file = temp_file_mp4
        
        # Get safe title for final filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", info.get('title', 'video'))
        output_filename = os.path.join(target_folder, f"{safe_title}.mp4")
        if os.path.exists(output_filename):
            try: os.remove(output_filename)
            except: pass
        
        if not os.path.exists(temp_file):
            # Fallback: search for file with download_id
            for file in os.listdir(temp_folder):
                if download_id in file and (file.endswith('.mp4') or file.endswith('.mkv') or file.endswith('.webm')):
                    temp_file = os.path.join(temp_folder, file)
                    break
            else:
                raise Exception("Could not find downloaded video file")
        
        # Move to final location
        if temp_file != output_filename:
            os.rename(temp_file, output_filename)
        
        # Cleanup any remaining temp files
        try:
            for file in os.listdir(temp_folder):
                if download_id in file:
                    temp_file = os.path.join(temp_folder, file)
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
        except: pass

        return output_filename

if __name__ == '__main__':
    app.run(debug=True)
