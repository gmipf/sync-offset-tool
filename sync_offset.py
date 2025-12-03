#!/usr/bin/env python3
import subprocess
import numpy as np
import sys
import json
import signal
import multiprocessing as mp
from scipy.signal import correlate

# --- Styling helpers ---
def warn_line(message):
    return f"\033[93m⚠️ {message}\033[0m"

def error_line(message):
    return f"\033[91m❌ {message}\033[0m"

# Global to hold worker process reference
_worker_proc = None

def _install_sigint_handler():
    """Install SIGINT handler that terminates worker if present."""
    def _handle_sigint(sig, frame):
        global _worker_proc
        if _worker_proc is not None and _worker_proc.is_alive():
            try:
                _worker_proc.terminate()
            except Exception:
                pass
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, _handle_sigint)

def get_track_index(mkvfile, lang="eng"):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index:stream_tags=language",
        "-of", "json", mkvfile
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        if stream.get("tags", {}).get("language", "").lower() == lang.lower():
            return stream["index"]
    raise RuntimeError(f"No {lang} audio track found in {mkvfile}")

def extract_pcm_to_array(mkvfile, track_index, sr=48000, duration=120, start=0):
    cmd = [
        "ffmpeg", "-ss", str(start), "-i", mkvfile,
        "-map", f"0:{track_index}", "-ac", "1", "-ar", str(sr),
        "-af", f"atrim=0:{duration}", "-f", "f32le", "pipe:1"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    data = np.frombuffer(proc.stdout, dtype=np.float32)
    print(f"Extracted {len(data)} samples from {mkvfile}")
    return data

def get_runtime(mkvfile):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mkvfile
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    seconds = float(result.stdout.strip())
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

def get_fps(mkvfile):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mkvfile
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rate = result.stdout.strip()
    if "/" in rate:
        num, denom = rate.split("/")
        fps = float(num) / float(denom)
    else:
        fps = float(rate)
    return f"{fps:.3f} fps"

def _direct_worker(sig1, sig2, sr, out_queue):
    corr = correlate(sig1, sig2, mode="full", method="direct")
    lag = np.argmax(corr) - (len(sig2) - 1)
    delay_ms = lag / sr * 1000
    peak_corr = corr[np.argmax(corr)] / len(sig1)
    out_queue.put((delay_ms, peak_corr))

def compute_offset(sig1, sig2, sr, method="fft", duration=120):
    sig1 = (sig1 - np.mean(sig1)) / (np.std(sig1) + 1e-9)
    sig2 = (sig2 - np.mean(sig2)) / (np.std(sig2) + 1e-9)
    min_len = min(len(sig1), len(sig2))
    sig1, sig2 = sig1[:min_len], sig2[:min_len]

    if method == "direct":
        if duration > 60:
            ans = input(warn_line(f"Direct correlation on {duration}s slice may be very slow. Continue? [y/N]: "))
            if ans.strip().lower() != "y":
                print(error_line("Aborted by user."))
                sys.exit(1)

        out_queue = mp.Queue()
        global _worker_proc
        _worker_proc = mp.Process(target=_direct_worker, args=(sig1, sig2, sr, out_queue), daemon=True)
        _worker_proc.start()
        try:
            while True:
                try:
                    result = out_queue.get(timeout=0.2)
                    break
                except Exception:
                    if not _worker_proc.is_alive():
                        raise RuntimeError("Direct correlation worker exited unexpectedly.")
            return result
        except KeyboardInterrupt:
            print(error_line("Interrupted by user (Ctrl+C). Terminating direct worker."))
            try:
                if _worker_proc.is_alive():
                    _worker_proc.terminate()
            except Exception:
                pass
            _worker_proc.join(timeout=1.0)
            _worker_proc = None
            sys.exit(1)
        finally:
            if _worker_proc is not None:
                _worker_proc.join(timeout=1.0)
                _worker_proc = None
    else:
        corr = correlate(sig1, sig2, mode="full", method="fft")
        lag = np.argmax(corr) - (len(sig2) - 1)
        delay_ms = lag / sr * 1000
        peak_corr = corr[np.argmax(corr)] / len(sig1)
        return delay_ms, peak_corr

def main():
    _install_sigint_handler()

    if len(sys.argv) < 3:
        print("Usage: sync_offset.py original.mkv async.mkv [lang1] [lang2] [duration_seconds] [start_seconds] [method]")
        sys.exit(1)

    sr = 48000
    lang1 = sys.argv[3] if len(sys.argv) > 3 else "eng"
    lang2 = sys.argv[4] if len(sys.argv) > 4 else "eng"
    duration = int(sys.argv[5]) if len(sys.argv) > 5 else 120
    start = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    method = sys.argv[7] if len(sys.argv) > 7 else "fft"

    try:
        orig_index = get_track_index(sys.argv[1], lang1)
        async_index = get_track_index(sys.argv[2], lang2)

        orig_data = extract_pcm_to_array(sys.argv[1], orig_index, sr, duration, start)
        async_data = extract_pcm_to_array(sys.argv[2], async_index, sr, duration, start)

        # New runtime + FPS reporting
        orig_runtime = get_runtime(sys.argv[1])
        async_runtime = get_runtime(sys.argv[2])
        orig_fps = get_fps(sys.argv[1])
        async_fps = get_fps(sys.argv[2])

        print(f"Runtime (original): {orig_runtime} | FPS: {orig_fps}")
        print(f"Runtime (async):    {async_runtime} | FPS: {async_fps}")

        offset_ms, peak_corr = compute_offset(orig_data, async_data, sr, method, duration)
        print(f"Best alignment offset: {offset_ms:.2f} ms")
        print(f"Peak correlation strength: {peak_corr:.4f}")
    except KeyboardInterrupt:
        # Already handled inside compute_offset
        pass

if __name__ == "__main__":
    try:
        mp.set_start_method("fork")
    except RuntimeError:
        pass
    main()
