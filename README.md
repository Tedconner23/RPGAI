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

This will open a web interface where you can chat with the AI. The sidebar shows a sample player's stats and inventory. Replace the `DummyClient` with an actual OpenAI client and API key for real interactions.
