"""CSV parsing for Spotify track lists."""

import csv
import io


def _find_column(fieldnames, *candidates):
    for name in fieldnames or []:
        if name and any(c in name.lower() for c in candidates):
            return name
    return None


def parse_csv(text):
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    track_col = _find_column(reader.fieldnames, "track", "title", "song", "name")
    artist_col = _find_column(reader.fieldnames, "artist")
    if not track_col or not artist_col:
        raise ValueError("CSV must have a track column and an artist column")
    for record in reader:
        track = (record.get(track_col) or "").strip()
        artist = (record.get(artist_col) or "").strip()
        if track:
            rows.append({"track": track, "artist": artist})
    return rows


def build_query(row):
    track = row.get("track", "").strip()
    artist = row.get("artist", "").strip()
    return f'"{track}" "{artist}"'.strip()
