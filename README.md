# Oh Roji - Bot

A Discord study helper bot built to support classmates and especially international students by providing quiz-style questions, review links, and useful helper commands.

This project started as a way to:
- Learn how to build a Discord bot using Python
- Create a Quizlet-style study tool for my program
- Share AME-related review questions (Intro to CARs, Metallurgy, Theory of Flight, etc.)
- Help international students and classmates review material more easily inside Discord

## Features

- Slash commands for starting quizzes
- Question banks organized by **course** and **week**
- Automatic scoring and feedback
- Study links to Google Docs notes
- Fun GIF reactions using media links
- Direct messages to welcome new members and explain how to use the bot

## Requirements

- Python 3.11+ (recommended)
- A Discord bot token
- A Discord server where you have permission to add bots

### Python packages

These are listed in `requirements.txt`:
- discord.py
- python-dotenv

## Setup

1. **Clone or download** this repository.

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root folder (same place as `Oh_Roji.py`) with:
   ```env
   DISCORD_BOT_TOKEN=your-bot-token-here
   ```

5. **Run the bot:**
   ```bash
   python Oh_Roji.py
   ```

6. Invite the bot to your server using the OAuth URL from the Discord Developer Portal.

## Notes

- The actual quiz questions are stored in `Question_Banks/` for:
  - Intro to CARs
  - Metallurgy
  - Theory of Flight
- You can edit or add new questions directly to those files.
- Do **not** commit your real `.env` file or bot token publicly.

## Author

Built by Rey as a personal learning project and a tool to help classmates and international students study more easily.
