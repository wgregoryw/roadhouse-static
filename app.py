import sys
sys.path.append("./src")
from flask import Flask, render_template_string
from datetime import datetime, date, timedelta
import requests
import urllib.parse
import json
import os
import shutil
import re

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>KEXP Playlist</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background: #eee; }
        img { max-width: 60px; }
        .comment { font-size: 0.95em; color: #444; }
        .audio-section { margin-bottom: 2em; }
        .playlist-table { margin-bottom: 2em; }
        .show-btn { margin-bottom: 1em; }
    </style>
    <script>
      function togglePlaylist(id) {
        var el = document.getElementById(id);
        if (el.style.display === "none") {
          el.style.display = "block";
        } else {
          el.style.display = "none";
        }
      }
    </script>
</head>
<body>
    <div class="audio-section">
        <h1>The Roadhouse – Listen to Recent Shows</h1>
        {% for show in recent_shows %}
          <h2>{{ show.date }}</h2>
          <audio controls style="width:100%;margin-bottom:1em;">
            <source src="{{ show.url }}" type="audio/mpeg">
            Your browser does not support the audio element.
          </audio>
          <p><a href="{{ show.url }}">Download MP3</a></p>
          <button class="show-btn" onclick="togglePlaylist('playlist-{{ show.id }}')">Show/Hide Playlist</button>
          <div id="playlist-{{ show.id }}" style="display:none;">
            <table class="playlist-table">
                <tr>
                    <th>Time</th>
                    <th>Art</th>
                    <th>Title</th>
                    <th>Artist</th>
                    <th>Album</th>
                    <th>Year/Label</th>
                    <th>Comment</th>
                </tr>
                {% for song in show.songs %}
                <tr>
                    <td>{{ song.time }}</td>
                    <td>
                        {% if song.art_url %}
                            <img src="{{ song.art_url }}" onerror="this.style.display='none';">
                        {% endif %}
                    </td>
                    <td>
                        <a href="{{ song.spotify_url }}" target="_blank" rel="noopener">
                            {{ song.title }}
                        </a>
                    </td>
                    <td>{{ song.artist }}</td>
                    <td>{{ song.album }}</td>
                    <td>{{ song.year_label }}</td>
                    <td class="comment">{{ song.comment }}</td>
                </tr>
                {% endfor %}
            </table>
          </div>
        {% endfor %}
    </div>
    <div class="audio-section">
        <h2>Archived Playlists (Last 2 Months)</h2>
        {% for show in archive_shows %}
          <div style="margin-bottom:1.5em;">
            <b>{{ show.date }}</b><br>
            <!-- No audio or download link for archive shows -->
            <button class="show-btn" onclick="togglePlaylist('playlist-{{ show.id }}')">Show/Hide Playlist</button>
            <div id="playlist-{{ show.id }}" style="display:none;">
              <table class="playlist-table">
                  <tr>
                      <th>Time</th>
                      <th>Art</th>
                      <th>Title</th>
                      <th>Artist</th>
                      <th>Album</th>
                      <th>Year/Label</th>
                      <th>Comment</th>
                  </tr>
                  {% for song in show.songs %}
                  <tr>
                      <td>{{ song.time }}</td>
                      <td>
                          {% if song.art_url %}
                              <img src="{{ song.art_url }}" onerror="this.style.display='none';">
                          {% endif %}
                      </td>
                      <td>
                          <a href="{{ song.spotify_url }}" target="_blank" rel="noopener">
                              {{ song.title }}
                          </a>
                      </td>
                      <td>{{ song.artist }}</td>
                      <td>{{ song.album }}</td>
                      <td>{{ song.year_label }}</td>
                      <td class="comment">{{ song.comment }}</td>
                  </tr>
                  {% endfor %}
              </table>
            </div>
          </div>
        {% endfor %}
    </div>
</body>
</html>
"""

ARCHIVE_CACHE_FILE = "archive_playlists.json"
ART_DIR = "static/art"
DOWNLOADS_DIR = "downloads"

def save_archive_cache(data):
    with open(ARCHIVE_CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_archive_cache():
    if os.path.exists(ARCHIVE_CACHE_FILE):
        with open(ARCHIVE_CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def download_image(url, filename):
    if not url:
        return None
    os.makedirs(ART_DIR, exist_ok=True)
    local_path = os.path.join(ART_DIR, filename)
    if not os.path.exists(local_path):
        try:
            resp = requests.get(url, stream=True, timeout=10)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    shutil.copyfileobj(resp.raw, f)
                return local_path
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None
    return local_path

def download_mp3(url, show_date_str):
    if not url:
        return None
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    # Use "The Roadhouse - YYYY-MM-DD.mp3" as filename
    filename = f"The Roadhouse - {show_date_str}.mp3"
    local_path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(local_path):
        try:
            resp = requests.get(url, stream=True, timeout=30)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"Downloaded: {local_path}")
                return local_path
            else:
                print(f"Failed to download {url}: status {resp.status_code}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None
    else:
        print(f"Already downloaded: {local_path}")
    return local_path

def sanitize_filename(s):
    # Remove or replace invalid filename characters
    return re.sub(r'[\\/*?:"<>|]', "_", s)

def format_song(item, local_art=False):
    # Format time as am/pm
    airdate = item.get("airdate", "")
    if airdate:
        try:
            dt = datetime.fromisoformat(airdate)
            time_str = dt.strftime("%I:%M %p").lstrip("0")
        except Exception:
            time_str = airdate[11:16]
    else:
        time_str = ""
    # Format labels
    labels = item.get("labels", [])
    if isinstance(labels, list):
        labels = ", ".join(labels)
    else:
        labels = str(labels)
    # Year from release_date
    release_date = item.get("release_date", "")
    year = release_date.split("-")[0] if release_date else ""
    # Spotify URL
    song = item.get("song", "")
    artist = item.get("artist", "")
    spotify_query = urllib.parse.quote(f"{song} {artist}")
    spotify_url = f"https://open.spotify.com/search/{spotify_query}"
    art_url = item.get("image_uri", "")
    if local_art and art_url:
        ext = os.path.splitext(art_url)[-1].split("?")[0]
        filename = sanitize_filename(f"{artist}_{song}_{year}{ext}")
        local_path = download_image(art_url, filename)
        if local_path:
            art_url = f"/static/art/{filename}"
    return {
        "time": time_str,
        "title": song,
        "artist": artist,
        "album": item.get("album", ""),
        "year_label": f"{year} {labels}".strip(),
        "art_url": art_url,
        "comment": item.get("comment", ""),
        "spotify_url": spotify_url,
    }

@app.route("/")
def index():
    # Get all Sundays from April 2025 through the most recent Sunday in June 2025
    sundays = []
    d = date(2025, 4, 1)
    while d.weekday() != 6:
        d += timedelta(days=1)
    last_sunday = get_last_two_sundays()[0]
    while d <= last_sunday:
        sundays.append(d)
        d += timedelta(days=7)

    # Split into recent (top 2) and archive (rest, last 2 months)
    recent_sundays = sundays[-2:]
    archive_cutoff = last_sunday - timedelta(days=60)
    archive_sundays = [s for s in sundays[:-2] if s >= archive_cutoff]

    def build_show_list(show_dates, local_art=False):
        shows = []
        for show_date in reversed(show_dates):  # Most recent first
            digit = get_roadhouse_digit(show_date)
            url = build_roadhouse_url(show_date, digit)
            date_str = show_date.strftime("%Y-%m-%d")
            start_dt = f"{date_str}T09:00:00-07:00"
            end_dt = f"{date_str}T12:00:00-07:00"
            api_results = fetch_roadhouse_playlist(start_dt, end_dt)
            songs = [format_song(item, local_art=local_art) for item in api_results]
            songs = list(reversed(songs))
            shows.append({
                "date": show_date.strftime("%B %d, %Y"),
                "url": url,
                "songs": songs,
                "id": show_date.strftime("%Y%m%d")
            })
        return shows

    # Recent shows are always live
    recent_shows = build_show_list(recent_sundays)

    # Download the two available MP3s if not already present
    for show in recent_shows:
        url = show["url"]
        # show["date"] is like "June 15, 2025", convert to YYYY-MM-DD
        show_date_str = datetime.strptime(show["date"], "%B %d, %Y").strftime("%Y-%m-%d")
        download_mp3(url, show_date_str)

    # Archive shows: cache to disk and download art locally
    archive_shows = load_archive_cache()
    if archive_shows is None:
        archive_shows = build_show_list(archive_sundays, local_art=True)
        save_archive_cache(archive_shows)

    return render_template_string(TEMPLATE, recent_shows=recent_shows, archive_shows=archive_shows)

def build_roadhouse_url(date, digit=6):
    ymd = date.strftime("%Y%m%d")
    filename = f"{ymd}08500{digit}-30-1961-the-roadhouse.mp3"
    return f"https://kexp-archive.streamguys1.com/content/kexp/{filename}"

def find_valid_roadhouse_url(date):
    for digit in range(6, 9):  # Try 6, 7, 8
        url = build_roadhouse_url(date, digit)
        try:
            r = requests.head(url, timeout=5)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return None

def get_roadhouse_digit(target_date, base_date=date(2025, 6, 8), base_digit=6):
    """Calculate the digit after 08500 for a given show date."""
    delta_weeks = (target_date - base_date).days // 7
    return base_digit + delta_weeks

def get_last_two_sundays():
    today = date.today()
    # Find the most recent Sunday
    offset = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=offset)
    prev_sunday = last_sunday - timedelta(days=7)
    return [last_sunday, prev_sunday]

@app.route("/listen")
def listen():
    sundays = get_last_two_sundays()
    shows = []
    for show_date in sundays:
        digit = get_roadhouse_digit(show_date)
        url = build_roadhouse_url(show_date, digit)
        shows.append({"date": show_date.strftime("%B %d, %Y"), "url": url})
    return render_template_string("""
    <h1>The Roadhouse – Listen to Recent Shows</h1>
    {% for show in shows %}
      <h2>{{ show.date }}</h2>
      <audio controls style="width:100%;margin-bottom:1em;">
        <source src="{{ show.url }}" type="audio/mpeg">
        Your browser does not support the audio element.
      </audio>
      <p><a href="{{ show.url }}">Download MP3</a></p>
    {% endfor %}
    """, shows=shows)

def fetch_roadhouse_playlist(start_dt, end_dt, max_pages=5):
    base_url = (
        "https://api.kexp.org/v2/plays/"
        f"?airdate_after={start_dt}"
        f"&airdate_before={end_dt}"
        "&show=The%20Roadhouse"
    )
    results = []
    url = base_url
    page_count = 0
    while url and page_count < max_pages:
        print("KEXP API URL:", url)
        resp = requests.get(url)
        data = resp.json()
        results.extend(data["results"])
        url = data.get("next")
        page_count += 1
    return results

if __name__ == "__main__":
    app.run(debug=True)