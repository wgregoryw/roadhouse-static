from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def scrape_kexp_playlist(month, day, year, hours, ampm="AM"):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    songs = []

    def build_kexp_url(month, day, year, hour, minute, ampm, location=3):
        base_url = "https://kexp.org/playlist/"
        query = (
            f"?location={location}"
            f"&month={month}"
            f"&day={day}"
            f"&year={year}"
            f"&hour={hour}:{minute:02d}"
            f"&ampm={ampm}"
        )
        return base_url + query

    for hour in hours:
        url = build_kexp_url(month, day, year, hour, 0, ampm)
        driver.get(url)
        time.sleep(5)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        for item in soup.select('.PlaylistItem.u-mb1'):
            time_tag = item.select_one('.PlaylistItem-time h5')
            time_val = time_tag.get_text(strip=True) if time_tag else None

            title_tag = item.select_one('.PlaylistItem-primaryContent h3')
            title = title_tag.get_text(strip=True) if title_tag else None

            artist_tag = item.select_one('.PlaylistItem-primaryContent .u-h3')
            artist = artist_tag.get_text(strip=True) if artist_tag else None

            album_tag = item.select_one('.PlaylistItem-primaryContent .u-h5.u-italic')
            album = album_tag.get_text(strip=True) if album_tag else None

            year_label_tag = item.select_one('.PlaylistItem-primaryContent .u-h5:not(.u-italic)')
            year_label = year_label_tag.get_text(strip=True) if year_label_tag else None

            art_tag = item.select_one('.PlaylistItem-image img')
            art_url = art_tag['src'] if art_tag and art_tag.has_attr('src') else None

            comment_tag = item.select_one('.PlaylistItem-secondaryContent p')
            comment = comment_tag.get_text(" ", strip=True) if comment_tag else None

            songs.append({
                "time": time_val,
                "title": title,
                "artist": artist,
                "album": album,
                "year_label": year_label,
                "art_url": art_url,
                "comment": comment,
            })
    driver.quit()
    return songs

month = "June"
day = 15
year = 2025
show_hours = [9, 10, 11]  # 9am, 10am, 11am

playlists = scrape_kexp_playlist(month, day, year, show_hours)
for song in playlists:
    print(song)