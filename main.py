"""Streamlit interface for the RPG AI project."""

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
import sys
from pathlib import Path
import openai
import logging

# Ensure the script is executed within Streamlit.
if get_script_run_ctx() is None:
    sys.exit("Error: This script must be run using 'streamlit run main.py'.")

logging.basicConfig(level=logging.INFO)

from rpg_ai.chat import ChatManager
from rpg_ai.game import GameState
from rpg_ai.models import Item, Player
from rpg_ai.utils import (
    load_source_files,
    upload_source_files,
    load_system_config,
)


def load_openai_client() -> openai.OpenAI:
    """Load the OpenAI client using the API key from the ``key`` folder."""
    key_dir = Path(__file__).parent / "key"
    key_files = list(key_dir.glob("*.key"))
    if not key_files:
        raise FileNotFoundError("No .key file found in 'key' directory.")
    api_key = key_files[0].read_text().strip()
    return openai.OpenAI(api_key=api_key)


def init_game() -> GameState:
    """Initialize a default game state with a sample player and items."""

    player = Player(name="Hero", race="Human", character_class="Fighter")
    player.add_item(
        Item(
            name="Sword",
            description="A trusty blade for close combat.",
            image_url="https://via.placeholder.com/150",
        )
    )
    player.add_item(
        Item(
            name="Shield",
            description="Protects against incoming attacks.",
            image_url="https://via.placeholder.com/150",
        )
    )

    source_dir = Path(__file__).parent / "source"
    source_text = load_source_files(source_dir)

    config_dir = Path(__file__).parent / "config"
    instructions, rating = load_system_config(config_dir)

    return GameState(
        player,
        source_text=source_text,
        instructions=instructions,
        rating=rating,
    )


if "game" not in st.session_state:
    st.session_state.game = init_game()

if "chat" not in st.session_state:
    client = load_openai_client()
    source_dir = Path(__file__).parent / "source"
    file_ids = upload_source_files(client, source_dir)
    st.session_state.chat = ChatManager(client, st.session_state.game, file_ids=file_ids)


left_col, right_col = st.columns([3, 1])

with left_col:
    st.title("RPG AI Chat")

    for entry in st.session_state.chat.history:
        role = entry["role"]
        content = entry["content"]
        if role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**AI:** {content}")

    user_input = st.text_input("Your message")
    if st.button("Send") and user_input:
        st.session_state.chat.send_message(user_input)
        # In Streamlit 1.25 and later, ``st.rerun`` replaces the experimental
        # ``st.experimental_rerun``. Using the newer API avoids an
        # ``AttributeError`` on newer versions of Streamlit.
        st.rerun()

with right_col:
    st.header("Player Info")
    player = st.session_state.game.player
    st.markdown(f"**Name:** {player.name}")
    st.markdown(f"**Race:** {player.race}")
    st.markdown(f"**Class:** {player.character_class}")
    st.markdown(f"**Level:** {player.level}")
    st.markdown(f"**HP:** {player.hit_points}")

    st.header("Inventory")
    for item in player.inventory:
        if item.image_url:
            st.image(item.image_url, width=80)
        st.markdown(f"**{item.name}** - {item.description}")
