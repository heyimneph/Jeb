# Jeb Discord Bot

A multi-purpose Discord bot featuring music playback, mini-games, birthday reminders and server administration utilities.

## Requirements

- Python 3.12 or later
- `ffmpeg`, `ffplay` and `ffprobe` available on your system or placed in the project directory. You can obtain these binaries from [ffmpeg.org](https://ffmpeg.org/).

## Installation

1. Clone the repository
2. Install the dependencies with `pip install -r requirements.txt`
3. Ensure the FFmpeg binaries are accessible as described above

## Configuration

Create a `.env` file with your bot token:

```env
DISCORD_TOKEN="YOUR TOKEN"
```

## Running the Bot

Run the bot directly with:

```bash
python bot.py
```

Or build and run using the provided `Dockerfile`:

```bash
docker build -t jeb-bot .
docker run --env-file .env jeb-bot
```

## Tests

Execute the test suite with:

```bash
pytest -q
```

## License

This project is licensed under the GNU GPLv3. See the [LICENSE](LICENSE) file for details.

