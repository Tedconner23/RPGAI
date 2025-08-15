# RPG AI Project

This project aims to build a role-playing game interface based on **Dungeons & Dragons 5e** mechanics. Gameplay centers on a chat conversation with an AI model. The Streamlit UI displays inventory, player stats, and other world information alongside the chat.

## Features

- **Chat-based gameplay** using the OpenAI API.
- **Python** implementation with third-party packages as needed.
- **Streamlit UI** showing text interactions and additional game information (images, stats, etc.).

## Running

Install dependencies and start the Streamlit application:

```bash
pip install -r requirements.txt
streamlit run main.py
```

If your shell cannot find the `streamlit` command, invoke it via Python instead:

```bash
python -m streamlit run main.py
```

If you encounter an error such as `ModuleNotFoundError: No module named 'streamlit.cli'`,
make sure Streamlit is installed and up to date:

```bash
pip install --upgrade streamlit
```

This will open a web interface where you can chat with the AI. Place your
OpenAI API key in a file with the `.key` extension inside a folder named
`key` (for example `key/openai.key`). The application reads this key and uses
the `gpt-4o` model for responses. The sidebar shows a sample player's stats and
inventory.

Any text, C# (`.cs`) or PDF files placed anywhere under a folder named
`source` (including subfolders) are automatically read and uploaded to the
OpenAI Assistants API at startup. The assistant can then search these files
for relevant information while responding to you.

The code attempts to support both old and new versions of the OpenAI client.
If you use a newer release that relies on vector stores for retrieval, the
application will create a temporary vector store and attach your uploaded files
to it automatically.

## Custom System Instructions

Place a file named `system.json` inside a folder called `config` to control the
assistant's behavior. The file should contain JSON with two optional fields:

- `instructions` – text prepended to the game description so you can guide how
  the AI responds.
- `rating` – a freeform string describing the desired content rating or
  explicitness level.

Example `config/system.json`:

```json
{
  "instructions": "You are a friendly dungeon master. Stay in character.",
  "rating": "PG-13"
}
```
