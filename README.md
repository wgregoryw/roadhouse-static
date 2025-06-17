# Roadhouse Static Site

## Overview

This project generates a static website for "The Roadhouse," a KEXP radio show. It uses Python and Flask to fetch recent and archived playlists, display show information, and cache album art locally. The site is built and deployed automatically to GitHub Pages using GitHub Actions.

## Features

- Displays the two most recent Roadhouse shows with streaming audio and playlists.
- Archives playlists from the last two months (playlist only, no audio).
- Album art is downloaded and served locally for fast, reliable display.
- Static site is generated with Flask and deployed via GitHub Actions.
- No copyrighted audio is stored or served—audio streams link directly to KEXP.

## Installation

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd Roadhouse
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

To generate the static site locally:
```sh
python generate_static.py
```
The output will be in the `output/` directory.

To run the Flask app for development:
```sh
python app.py
```

## Deployment

Static site deployment is automated with GitHub Actions. On each push (or weekly), the site is rebuilt and published to GitHub Pages from the `gh-pages` branch.

## Contributing

Contributions and suggestions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.