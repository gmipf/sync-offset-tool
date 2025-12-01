# Sync Offset Tool

A command‑line utility to measure audio sync offsets between two MKV files. It extracts audio tracks, cross‑correlates them, and reports the best alignment offset in milliseconds.

## Features
- 🎵 Audio extraction: Uses ffmpeg to pull raw PCM samples directly from MKV audio tracks.
- ⚡ Fast correlation: Defaults to FFT‑based cross‑correlation for speed.
- 🧮 Direct correlation option: More precise but slower; runs in a separate worker process so you can interrupt safely.

## Requirements
- Python 3.8+
- NumPy
- SciPy
- FFmpeg installed and available in your PATH

## Usage
`./sync_offset.py original.mkv async.mkv [lang1] [lang2] [duration_seconds] [start_seconds] [method]`

Arguments:
- `original.mkv` — reference file
- `async.mkv` — file suspected of being out of sync
- `lang1` — language code for original track (default: eng)
- `lang2` — language code for async track (default: eng)
- `duration_seconds` — slice length to analyze (default: 120)
- `start_seconds` — offset into the file to start slice (default: 0)
- `method` — correlation method: fft (default) or direct

## Examples
Run FFT correlation on a 120‑second slice from the start, English vs English (default):
`./sync_offset.py movie1.mkv movie2.mkv`

Analyze a German audio track against an English one for 90 s:
`./sync_offset.py movie1.mkv movie2.mkv deu eng 90`

Run FFT correlation on a long 300‑second slice starting at 600 s:
`./sync_offset.py movie1.mkv movie2.mkv eng eng 300 600 fft`

Compare 10‑second slices starting at 320 s using direct correlation:
`./sync_offset.py movie1.mkv movie2.mkv eng eng 10 320 direct`

## Output
- Best alignment offset: Reported in milliseconds. Positive means the async file lags behind the original.
- Peak correlation strength: Value between 0 and 1 indicating match quality.
  Higher values mean a stronger match and therefore better confidence in the measured offset.

### Interpreting correlation strength
- **> 0.80** → Excellent match, high confidence in the offset measurement
- **0.50 – 0.80** → Moderate match, offset is usable but less certain
- **< 0.50** → Weak match, results may be unreliable (consider shorter slices or different segments)

## Tips for Better Results
- Choose slices with **dialogue, sharp sounds, or clear audio events** — they produce stronger correlations than background noise or music alone.
- Use **shorter slices (10–60 s)** if correlation strength is weak; smaller segments often align more clearly.
- Try analyzing **different parts of the file** (e.g., start, middle, end) to confirm consistency of offsets.

## Notes
- Use FFT mode for long slices — it’s much faster.
- Use Direct mode only for short slices or when you need maximum precision.
- The script will refuse to run direct mode on slices >60 s without confirmation.
- On interruption, the worker process is terminated immediately — no orphan processes left behind.

## Troubleshooting
- No audio track found: Check the language codes (eng, deu, fra, etc.) with ffprobe.
- FFmpeg errors: Ensure ffmpeg and ffprobe are installed and accessible in your PATH.
- Negative offsets: A negative offset means the async file is ahead of the original.
- Performance: Direct mode is O(n²). For slices longer than ~30 s, prefer FFT mode.
