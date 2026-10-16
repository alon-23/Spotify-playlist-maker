# Spotify Playlist Maker — Design

**Date:** 2026-10-16
**Status:** Approved

## Goal

A local web app that reads a CSV of tracks (Track, Artist, Album, Spotify Search
URL), matches each track through the Spotify Search API, creates a playlist, and
reports tracks it could not match.

## Constraints & decisions

- **Single user, local only.** No deployment, no multi-user auth.
- **Spotify Web API** is the only supported way to create playlists programmatically.
  A desktop client cannot be injected directly. Auth uses the Authorization Code
  flow with a `http://localhost:5000/callback` redirect.
- **CSV has no track IDs**, only names + a search query URL. The app must search
  Spotify per track and accept the top result.
- **Unmatched handling:** add everything found; show a misses table with manual
  search links.
- **Playlist name:** text field pre-filled with the CSV filename (no extension),
  editable by the user.
- **GitHub-ready:** secrets kept out of the repo via a gitignored
  `spotify_maker.json`; README documents setup.

## Architecture

- `app.py` — Flask routes + request orchestration.
- `spotify.py` — Spotify API client (auth, search, playlist create, batched adds).
- `csv_tracks.py` — CSV parsing and search-query building.
- `config.py` — read/write the local JSON config.
- `static/index.html` — single page UI, vanilla JS.
- `test_parse.py` — unit checks for parsing/query logic.

## Data flow

CSV text → `parse_csv` → rows → `build_query` per row → `search_track` (top hit)
→ matched URIs / misses → user picks name → `create_playlist` → `add_tracks`
(batches of 100) → result with "Open in Spotify" link.

## Error handling

- 401 → refresh access token and retry once.
- 429 → honour `Retry-After`, back off, retry.
- Missing credentials / not connected / empty CSV → clear message in the UI.
- Small delay between searches to respect rate limits.

## Testing

- Unit: CSV parsing (well-formed, tolerant headers, missing columns, blank rows)
  and query building.
- Manual: one live run against a real Spotify account to verify search, playlist
  creation, and misses reporting.
