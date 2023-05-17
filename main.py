import io
import json
import re
import time
import asyncio

from pathlib import Path
from gtts import gTTS
from twitchio import Message
from twitchio.ext import commands
import pygame

# Load twitch credentials
credentials_path = Path("credentials.json")
credentials = json.loads(credentials_path.read_text())
twitch_twitch_token = credentials["token"]
twitch_initial_channels = credentials["initial_channels"]

# Initialize Pygame and Pygame.mixer
pygame.init()
pygame.mixer.init()


def should_read_message(message: Message) -> bool:
    if message.content.startswith("!bsr"):
        return False
    return True


repeated_letter_pattern = re.compile(r"(.)\1{2,}")


def message_event_to_text(message: Message) -> str:
    content = f"{message.author.display_name}: {message.content}"
    # limits repeated letters to maximum of 3
    content = repeated_letter_pattern.sub(r"\1\1\1", content)
    return content


# Define function to convert message to audio content
def tts_message_to_audio_content(message) -> io.BytesIO:
    # Set the language for the text-to-speech conversion
    lingua = "en"
    # Create a gTTS object with the message and language
    tts = gTTS(text=message, lang=lingua)
    # Create an empty byte stream to write the audio content to
    audio_content = io.BytesIO()
    # Write the audio content to the byte stream
    tts.write_to_fp(audio_content)
    # Set the byte stream position to the beginning
    audio_content.seek(0)
    # Return the byte stream containing the audio content
    return audio_content


# Define a Bot class that extends the commands.Bot class from the twitchio library
class Bot(commands.Bot):
    def __init__(self):
        # Call the constructor of the parent class with the Twitch API token and prefix
        # Also specify the initial channels to join
        super().__init__(
            token=twitch_twitch_token,
            prefix="?",
            initial_channels=[
                twitch_initial_channels,
            ],
        )

    # Define an event handler for when the bot is ready to start processing events
    async def event_ready(self):
        print(f"Logged in as | {self.nick}")

    # Define an event handler for when a message is received
    async def event_message(self, message: Message):
        if not should_read_message(message):
            return
        message_text = message_event_to_text(message)
        print(message_text)
        # get TTS audio
        audio_content = tts_message_to_audio_content(message_text)

        # wait for current message to finish
        retry_count = 0
        while pygame.mixer.music.get_busy():
            # intentionally use non-async sleep here, so that messages stay in order
            time.sleep(0.1)
            # await asyncio.sleep(0.100)
            retry_count += 1
        if retry_count > 0:
            print(f"warning: {retry_count=}")

        # Load the audio content for the message into the Pygame mixer
        pygame.mixer.music.load(audio_content)
        # Play the audio content
        pygame.mixer.music.play()


# Create an instance of the Bot class
bot = Bot()
# Start the bot
bot.run()

# Quit Pygame.mixer and Pygame
pygame.mixer.quit()
pygame.quit()
