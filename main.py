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

if "user_text" not in st.session_state:
    st.session_state.user_text = ""


st.title("RPG AI Chat")

top_cols = st.columns([2, 1, 1, 1])
if top_cols[0].button("New chat"):
    st.session_state.chat.clear()
    st.rerun()
regen_disabled = len(st.session_state.chat.history) < 2 or \
    st.session_state.chat.history[-1]["role"] != "assistant"
if top_cols[1].button("Regenerate", disabled=regen_disabled):
    st.session_state.chat.regenerate_last()
    st.rerun()
if top_cols[2].button("Clear chat"):
    st.session_state.chat.clear()
    st.rerun()
if top_cols[3].download_button(
    "Save chat", st.session_state.chat.export_history(), file_name="chat.txt"
):
    st.toast("Chat saved")

for i, entry in enumerate(st.session_state.chat.history):
    with st.chat_message(entry["role"]):
        st.code(entry["content"], language="", use_container_width=True)
        cols = st.columns([8, 1])
        cols[0].caption(entry["role"].capitalize())
        if cols[1].button("\u274C", key=f"rm_{i}", help="Remove from context"):
            st.session_state.chat.remove_message(i)
            st.rerun()

if st.session_state.chat.history and st.session_state.chat.history[-1]["role"] == "assistant":
    if st.button("Regenerate response", key="regen_bottom"):
        st.session_state.chat.regenerate_last()
        st.rerun()

def send_message() -> None:
    text = st.session_state.user_text.strip()
    if text:
        st.session_state.chat.send_message(text)
        st.session_state.user_text = ""

st.text_area("Your message", key="user_text", height=100)
st.button("Send", on_click=send_message)

with st.sidebar:
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
