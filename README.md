# Bhakti Shorts Automation

Production-ready Python project for automating a Hindi-only YouTube Shorts channel focused on Hindu devotional, spiritual, and Sanatan motivation content. This project is intentionally isolated so it can live separately from any fitness-channel automation stack.

## What It Does

- Generates original devotional Shorts ideas with a local trend bank and OpenAI enhancement
- Writes Hindi scripts in Devanagari only
- Produces Shorts SEO metadata optimized for India discovery
- Creates Hindi voiceovers with Edge TTS and falls back to gTTS
- Builds SRT subtitles automatically
- Renders vertical 1080x1920 Shorts with MoviePy
- Uses Pexels portrait visuals when requested and configured
- Mixes in local background music from `assets/music/` when available
- Stores history to reduce duplicate ideas and repeated topics
- Supports later YouTube upload via separate devotional OAuth/token settings
- Supports local scheduling plans for batching content

## Project Structure

```text
bhakti_shorts_automation/
├── assets/
│   ├── fonts/
│   └── music/
├── data/
├── logs/
├── output/
│   ├── audio/
│   ├── images/
│   ├── subtitles/
│   └── video/
├── config.py
├── idea_generator.py
├── llm_fallback.py
├── main.py
├── scheduler.py
├── script_generator.py
├── seo_generator.py
├── subtitle_generator.py
├── tts.py
├── upload_all.py
├── uploader.py
├── video_generator.py
├── viral_topics.py
├── commands_cheatsheet.txt
├── requirements.txt
└── .env.example
```

## Requirements

- Python 3.10+
- `ffmpeg` installed and available in PATH
- A Hindi-capable Devanagari font

Recommended font setup:

- Put `NotoSansDevanagari-Regular.ttf` or `NotoSerifDevanagari-Regular.ttf` into `assets/fonts/`
- On Windows, the project also tries `Nirmala.ttf`, `Mangal.ttf`, `Kokila.ttf`, and `Aparajita`

## Environment Setup

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Fill in the keys you have now.
5. Add `ffmpeg` to PATH.

Example:

```powershell
cd d:\yt-2\bhakti_shorts_automation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Supported `.env` Keys

The project reads only from `.env` and never hardcodes secrets:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `PEXELS_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `BHAKTI_YOUTUBE_API_KEY`
- `BHAKTI_YOUTUBE_CLIENT_SECRET_FILE`
- `BHAKTI_YOUTUBE_TOKEN_FILE`
- `UPLOAD_ENABLED`
- `LOG_LEVEL`

Notes:

- `ELEVENLABS_*` keys are accepted for future expansion, but current TTS uses Edge TTS first and gTTS fallback.
- `BHAKTI_YOUTUBE_API_KEY` is reserved for future devotional trend discovery from YouTube.
- Upload still works locally without YouTube credentials; it simply skips upload.

## How The Pipeline Works

1. `idea_generator.py`
   Creates emotionally powerful devotional ideas, using local trend logic first and OpenAI for stronger originality.
2. `script_generator.py`
   Converts an idea into a Hindi-only Devanagari script with a strong viral hook, emotional problem, insight, takeaway, and CTA.
3. `seo_generator.py`
   Generates title, description, hashtags, and tags with India-focused devotional search intent.
4. `tts.py`
   Produces Hindi narration.
5. `subtitle_generator.py`
   Generates `.srt` subtitles based on audio duration.
6. `video_generator.py`
   Renders a 9:16 Short with background visuals, top hook text, subtitles, narration, and optional music.
7. `uploader.py`
   Uploads later when devotional channel OAuth files are configured.
8. `scheduler.py`
   Saves a local publish plan for batch operations.

## Channel Strategy Defaults

- Default language: Hindi
- Script output: Devanagari only
- Shorts duration target: 30 to 45 seconds
- Tone: devotional, emotionally deep, respectful, cinematic, uplifting, intense when needed
- Safety filters:
  - no fake miracles
  - no misleading claims
  - no sectarian hate
  - no political propaganda
  - no medical or legal claims

## Pexels Visual Strategy

When `--use-pexels` is enabled and `PEXELS_API_KEY` exists, the system searches portrait-friendly spiritual/cinematic queries such as:

- `temple india`
- `shiva statue`
- `diya flame`
- `meditation india`
- `prayer hands`
- `temple bells`
- `mountains sunrise spiritual`
- `river aarti`
- `incense temple`
- `devotional crowd`

If nothing is downloaded, the system falls back to a premium-looking gradient background so video generation still succeeds.

## Commands

See `commands_cheatsheet.txt` for ready-to-run examples.

Main examples:

```powershell
python main.py --count 1
python main.py --count 2
python main.py --topic "महाकाल पर भरोसा क्यों सब बदल देता है"
python main.py --count 2 --upload
python main.py --schedule
python main.py --use-pexels
```

## Output Files

- Videos: `output/video/`
- Narration audio: `output/audio/`
- Subtitles: `output/subtitles/`
- Downloaded visuals: `output/images/`
- Logs: `logs/automation.log`
- Idea history: `data/idea_history.json`
- Content history: `data/content_history.json`
- Schedule queue: `data/schedule_queue.json`

Each generated Short also gets a `*_metadata.json` file next to the video so uploads can be retried later.

## Assumptions

- OpenAI is used for stronger ideas/scripts/SEO when configured.
- If OpenAI is unavailable, the local trend bank and fallback templates still keep the project runnable.
- If Pexels is unavailable, the renderer still creates a usable Short with a themed gradient background.
- If local music is unavailable, the Short is rendered with voice only.
- If upload credentials are missing, upload is skipped instead of failing the entire pipeline.

## Suggested Channel Names

1. Bhakti Tej Shorts
2. Mahakal Bhakti Feed
3. Sanatan Soul Shorts
4. Shraddha Jyoti
5. Divya Sankalp Shorts
6. Dharma Deep
7. Aastha Agni Shorts
8. Bhakti Shakti Studio
9. Rudra Prerna
10. Hari Kripa Shorts
11. Jai Mahadev Motion
12. Shakti Path Shorts
13. Sanatan Drishti
14. Bhav Se Bhakti
15. Adhyatmik Josh

## Practical Tips

- Add a clean devotional instrumental track to `assets/music/` for premium feel.
- Add a Devanagari font into `assets/fonts/` before production use.
- Review generated metadata before enabling upload at scale.
- For best retention, keep hooks extremely sharp and visually readable in under 2 seconds.

## Disclaimer

This project is optimized for devotional and spiritual motivational content. It is designed to remain respectful and avoid manipulative, deceptive, hateful, political, or harmful claims. You remain responsible for final review before publishing.
