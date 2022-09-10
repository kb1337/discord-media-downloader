import asyncio
import logging
import os
import random
import re
from datetime import datetime

import discord
import requests
from dotenv import load_dotenv

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


IMAGE_REGEX = r"https:\/\/cdn\.discordapp\.com\/attachments\/\d*\/\d*\/([a-z0-9\_\-\.]*)\.(jpg|jpeg|png)$"
VIDEO_REGEX = r"https:\/\/cdn\.discordapp\.com\/attachments\/\d*\/\d*\/([a-z0-9\_\-\.]*)\.(mp4|avi|mov)$"


def is_image(content: str) -> bool:
    return True if re.match(IMAGE_REGEX, str(content).lower()) else False


def is_video(content: str) -> bool:
    return True if re.match(VIDEO_REGEX, str(content).lower()) else False


def safe_string(text: str) -> str:
    result_text = ""
    for char in str(text):
        if char.isalnum() or char in ["-", "_", "."]:
            result_text += char

    return result_text


def format_date(datetime_instance: datetime) -> str:
    return datetime_instance.strftime("%Y-%m-%d_%H-%M-%S")


def create_folder(server_name: str, channel_name: str) -> str:
    current_path = os.getcwd()
    downloads_folder = os.path.join(current_path, r"..\downloads")
    downloads_folder = os.path.abspath(downloads_folder)

    server_name = safe_string(server_name)
    channel_name = safe_string(channel_name)
    datetime_str = format_date(datetime.now())
    folder_name = f"{server_name}_{channel_name}_{datetime_str}"

    path = os.path.join(downloads_folder, folder_name)

    if not os.path.exists(path):
        os.mkdir(path)
    return path


async def download_media(url: str, folder: str, file_name: str) -> None:
    logger.info("[*] Downloading %s as %s", url, file_name)
    path = os.path.join(folder, file_name)
    with open(path, "wb") as file:
        response = requests.get(url)
        file.write(response.content)
    logger.info("[+] Download Successfull.")


def convert_byte_to_mb(byte: int) -> float:
    return round(byte / 1024 / 1024, 3)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = ">"

    async def on_ready(self):
        logger.info("[*] %s is ALIVE!", self.user.name)

    async def on_message(self, message):
        if message.content[: len(self.prefix)] == self.prefix:
            command = message.content[len(self.prefix) :]
            is_admin = message.author.guild_permissions.administrator

            if message.author.bot:
                logger.info("[-] Robots can not give me orders!")
                return 0

            logger.info("[*] %s: %s: %s", format_date(datetime.now()), message.author, command)

            if command == "ping":
                latency = round(self.latency * 1000, 2)
                await message.channel.send(f"Latency: {latency}ms")
                logger.info("[+] Latency: %f ms", latency)

            elif command.startswith("scan"):
                if not is_admin:
                    await message.reply("This is admin only command.", delete_after=10)
                    logger.info("[-] Unauthorized")
                    return 0

                number_of_messages = (  # number of messages (newest to oldest)
                    int(command.split()[1])
                    if len(command.split()) > 1 and command.split()[1].isdigit()
                    else 5  # default: check last 5 messages.
                )

                message_history = [message async for message in message.channel.history(limit=number_of_messages)]

                images = {}
                videos = {}
                others = {}

                total_image_size = 0
                total_video_size = 0
                total_other_size = 0

                counter = 1
                for message in message_history:
                    if message.attachments and not message.author.bot:
                        for attachment in message.attachments:
                            logger.debug("[*] %d - %s: %s", counter, message.author.name, attachment)

                            file_extention = attachment.url.rsplit(".", maxsplit=1)[-1]
                            author = safe_string(str(message.author))
                            attachment_name = (
                                f"{counter:04d}_{format_date(message.created_at)}_{author}.{file_extention}"
                            )
                            attachment_size = convert_byte_to_mb(attachment.size)

                            if is_image(attachment):
                                logger.debug("[*] Image Size: %f mb", attachment_size)
                                total_image_size += attachment.size
                                images[str(attachment)] = attachment_name
                            elif is_video(attachment):
                                logger.debug("[*] Video Size: %f mb", attachment_size)
                                total_video_size += attachment.size
                                videos[str(attachment)] = attachment_name
                            else:
                                logger.debug("[*] Other Size: %f mb", attachment_size)
                                total_other_size += attachment.size
                                others[str(attachment)] = attachment_name

                            counter += 1

                logger.info("[+] %d images, %d videos, %d others", len(images), len(videos), len(others))
                logger.info("[+] Total Image Size: %f mb", convert_byte_to_mb(total_image_size))
                logger.info("[+] Total Video Size: %f mb", convert_byte_to_mb(total_video_size))
                logger.info("[+] Total Other Size: %f mb", convert_byte_to_mb(total_other_size))

                # Summary report message
                colors = [0xFF0000, 0xFFEE00, 0x40FF00, 0x00BBFF, 0xFF00BB]

                embed_message = discord.Embed(title="Report", color=random.choice(colors))
                embed_message.add_field(
                    name="Messages",
                    value=f"{len(message_history)} messages found.",
                    inline=False,
                )
                if total_image_size > 0:
                    media_size = convert_byte_to_mb(total_image_size)
                    embed_message.add_field(
                        name="Images",
                        value=f"{len(images)} images found. (Size: {media_size}mb)",
                        inline=False,
                    )
                if total_video_size > 0:
                    media_size = convert_byte_to_mb(total_video_size)
                    embed_message.add_field(
                        name="Videos",
                        value=f"{len(videos)} videos found. (Size: {media_size}mb)",
                        inline=False,
                    )
                if total_other_size > 0:
                    media_size = convert_byte_to_mb(total_other_size)
                    embed_message.add_field(
                        name="Others",
                        value=f"{len(others)} other type of medias found. (Size: {media_size}mb)",
                        inline=False,
                    )

                total_media_size = total_image_size + total_video_size + total_other_size
                embed_message.add_field(
                    name="Total Size of Medias",
                    value=f"{convert_byte_to_mb(total_media_size)}mb",
                    inline=False,
                )
                await message.channel.send(embed=embed_message)

                # Options (Images, Videos, All) message
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
                options = []

                if total_image_size > 0:
                    options.append("Images")
                if total_video_size > 0:
                    options.append("Videos")
                if total_other_size > 0:
                    options.append("Others")
                if len(options) > 1:
                    options.append("All")

                if options:
                    options_text = "__**Download Options**__"
                    for option in options:
                        options_text += f"\n[{options.index(option) + 1}] {option}"

                    options_message = await message.channel.send(options_text)

                    # Reactions for options
                    for i in range(len(options)):
                        await options_message.add_reaction(emojis[i])

                    options_emojis = [emojis[i] for i in range(len(options))]

                    # Handles multiple commands at the same time.
                    emoji = await self.react_message(
                        message,
                        options_message,
                        options_emojis,
                    )

                    if not emoji:
                        await options_message.delete()
                        return 0

                    # After author choose option
                    selection = options[options_emojis.index(emoji)]
                    status_message = await options_message.edit(content=f"Downloading {selection}...")

                    # Download Medias

                    server_name = options_message.guild.name if options_message.guild else "Server"
                    channel_name = options_message.channel.name if options_message.channel.name else "Channel"
                    folder = create_folder(server_name=server_name, channel_name=channel_name)

                    if selection == "Images":
                        for url, name in images.items():
                            await download_media(url, folder, name)
                    elif selection == "Videos":
                        for url, name in videos.items():
                            await download_media(url, folder, name)
                    elif selection == "Others":
                        for url, name in others.items():
                            await download_media(url, folder, name)
                    elif selection == "All":
                        for url, name in images.items():
                            await download_media(url, folder, name)
                        for url, name in videos.items():
                            await download_media(url, folder, name)
                        for url, name in others.items():
                            await download_media(url, folder, name)

                    await status_message.edit(content="Download Completed.", delete_after=10)

    async def react_message(
        self,
        command_message: discord.Message,
        options_message: discord.Message,
        options_emojis: list[str],
    ) -> str:
        # Check if the user is a command author.
        # Accept only emojis that the bot reacted
        def check(reaction, user):
            return (
                reaction.message.id == options_message.id
                and user == command_message.author
                and str(reaction.emoji) in options_emojis
            )

        # The bot waits for the author to choose option.
        try:
            reaction, *_ = await client.wait_for("reaction_add", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            logger.info("[-] User didn't react in time.")
            return ""
        else:
            return reaction.emoji


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN", "")
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(TOKEN)
