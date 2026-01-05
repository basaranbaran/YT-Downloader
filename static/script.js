document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultArea = document.getElementById('resultArea');
    const errorMsg = document.getElementById('errorMsg');
    const downloadBtn = document.getElementById('downloadBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    // Elements to populate
    const thumbnail = document.getElementById('thumbnail');
    const videoTitle = document.getElementById('videoTitle');
    const uploader = document.getElementById('uploader');
    const duration = document.getElementById('duration');
    const qualitySelect = document.getElementById('qualitySelect');
    const qualityGroup = document.getElementById('qualityGroup');
    const typeInputs = document.querySelectorAll('input[name="fileType"]');

    // Playlist Elements
    const playlistArea = document.getElementById('playlistArea');
    const playlistCount = document.getElementById('playlistCount');
    const modeInputs = document.querySelectorAll('input[name="downloadMode"]');
    const downloadBtnInfo = document.querySelector('#downloadBtn .btn-text');
    const successMessage = document.getElementById('successMessage');
    const successText = document.getElementById('successText');

    let currentUrl = '';
    let currentDownloadId = null;
    let abortController = null;

    // Fetch configuration (download path)
    fetchConfig();

    analyzeBtn.addEventListener('click', analyzeVideo);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') analyzeVideo();
    });

    typeInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            if (e.target.value === 'audio') {
                qualityGroup.style.display = 'none';
            } else {
                qualityGroup.style.display = 'block';
            }
        });
    });

    modeInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateDownloadButtonText();
        });
    });

    downloadBtn.addEventListener('click', downloadVideo);
    cancelBtn.addEventListener('click', cancelDownload);

    function updateDownloadButtonText() {
        const mode = document.querySelector('input[name="downloadMode"]:checked').value;
        if (mode === 'playlist') {
            downloadBtnInfo.textContent = 'Download Full Album';
        } else {
            downloadBtnInfo.textContent = 'Download Now';
        }
    }

    async function analyzeVideo() {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter a valid YouTube URL');
            return;
        }

        resetUI();
        setLoading(analyzeBtn, true);
        currentUrl = url;

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Failed to analyze video');

            // Populate UI
            videoTitle.textContent = data.title;
            // Use generic or specific info
            uploader.textContent = data.uploader || 'YouTube';
            duration.textContent = data.duration || '';
            thumbnail.src = data.thumbnail || '';

            // Playlist Handling
            if (data.is_playlist) {
                playlistArea.classList.remove('hidden');
                playlistCount.textContent = `${data.playlist_count} videos found`;
                // Select "playlist" mode by default for convenience if user pasted a playlist
                document.getElementById('modePlaylist').checked = true;
                updateDownloadButtonText();
            } else {
                document.getElementById('modeSingle').checked = true;
                updateDownloadButtonText();
            }

            // Populate resolutions
            qualitySelect.innerHTML = '';
            // If resolutions are returned, use them
            const resolutions = data.resolutions || ['1080p', '720p', '480p'];

            // Add "Best" option
            const bestOpt = document.createElement('option');
            bestOpt.value = 'best';
            bestOpt.textContent = 'Best Quality';
            qualitySelect.appendChild(bestOpt);

            resolutions.forEach(res => {
                // Ensure we strip 'p' for value if needed, or keep it consistent with backend
                // Backend sends "1080p", "720p". 
                // My backend logic in download() handles "1080" or "720" or "480".
                // I should strip 'p' for value or update backend to handle 'p'.
                // Easier to strip 'p' here for value.
                const val = res.replace('p', '');
                const opt = document.createElement('option');
                opt.value = val;
                opt.textContent = res; // Display "1080p"
                qualitySelect.appendChild(opt);
            });

            resultArea.classList.remove('hidden');

        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(analyzeBtn, false);
        }
    }

    async function downloadVideo() {
        if (!currentUrl) return;

        setLoading(downloadBtn, true);
        cancelBtn.classList.remove('hidden');
        currentDownloadId = null;
        abortController = new AbortController();

        const type = document.querySelector('input[name="fileType"]:checked').value;
        const quality = qualitySelect.value;
        const mode = document.querySelector('input[name="downloadMode"]:checked').value;

        // Reset Log if playlist
        if (mode === 'playlist') {
            document.getElementById('progressLog').classList.remove('hidden');
            document.getElementById('logContent').innerHTML = '';
            document.getElementById('progressStats').textContent = 'Initializing...';
        }

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: currentUrl,
                    type: type,
                    quality: quality,
                    mode: mode
                }),
                signal: abortController.signal
            });

            const contentType = response.headers.get('content-type');

            // Check for Stream (Playlist)
            if (contentType && contentType.includes('text/event-stream')) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let cancelled = false;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const jsonStr = line.replace('data: ', '').replaceAll("'", '"');
                                const data = JSON.parse(jsonStr);
                                
                                // Store download_id if present
                                if (data.download_id) {
                                    currentDownloadId = data.download_id;
                                }
                                
                                // Check if cancelled
                                if (data.status === 'cancelled') {
                                    cancelled = true;
                                    showError('Download cancelled');
                                    break;
                                }
                                
                                addLog(data);
                            } catch (e) {
                                console.log('Parse error', e, line);
                            }
                        }
                    }
                    
                    if (cancelled) break;
                }

                if (!cancelled) {
                    showSuccess('Album Downloaded Successfully!');
                }
                setLoading(downloadBtn, false);
                cancelBtn.classList.add('hidden');
                return;
            }

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Download failed');
            }

            // If blob (single file)
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) filename = match[1];
            } else {
                filename += (type === 'audio' ? '.mp3' : '.mp4');
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();

            const successMsg = type === 'audio' ? 'Song Downloaded Successfully!' : 'Video Downloaded Successfully!';
            showSuccess(successMsg);

        } catch (error) {
            if (error.name === 'AbortError') {
                showError('Download cancelled');
            } else {
                showError(error.message);
                if (mode === 'playlist') {
                    addLog({ status: 'error', message: error.message });
                }
            }
        } finally {
            setLoading(downloadBtn, false);
            cancelBtn.classList.add('hidden');
            currentDownloadId = null;
            abortController = null;
        }
    }

    async function cancelDownload() {
        if (abortController) {
            abortController.abort();
        }
        
        // Add cancellation message to log
        addLog({ 
            status: 'error', 
            message: 'Download cancelled by user' 
        });
        
        if (currentDownloadId) {
            try {
                await fetch('/api/cancel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ download_id: currentDownloadId })
                });
            } catch (e) {
                console.error('Failed to cancel download:', e);
            }
        }
        
        setLoading(downloadBtn, false);
        cancelBtn.classList.add('hidden');
        showError('Download cancelled');
    }

    function showSuccess(msg) {
        successText.textContent = msg;
        successMessage.classList.remove('hidden');
        setTimeout(() => successMessage.classList.add('hidden'), 5000);
    }

    function addLog(data) {
        const logContent = document.getElementById('logContent');
        const stats = document.getElementById('progressStats');

        const line = document.createElement('div');
        line.className = `log-line ${data.status}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${data.message}`;

        logContent.appendChild(line);
        logContent.scrollTop = logContent.scrollHeight;

        if (data.total) {
            stats.textContent = `${data.current}/${data.total}`;
        }
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        setTimeout(() => {
            errorMsg.textContent = '';
        }, 5000);
    }

    function resetUI() {
        resultArea.classList.add('hidden');
        playlistArea.classList.add('hidden'); // Hide playlist info on reset
        successMessage.classList.add('hidden'); // Hide success message
        errorMsg.textContent = '';
        updateDownloadButtonText();
    }

    function setLoading(btn, isLoading) {
        if (isLoading) {
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    async function fetchConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            if (data.download_path) {
                document.getElementById('downloadPath').textContent = data.download_path;
            }
        } catch (e) {
            console.error('Failed to fetch config', e);
        }
    }
});
