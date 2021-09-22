import discord, logging, os, re, wget, asyncio, random
from datetime import datetime
from dotenv import load_dotenv
from requests import get

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


image_regex = "https:\/\/cdn.discordapp.com\/attachments\/[0-9]*\/[0-9]*\/([a-zA-Z0-9\_\-\.]*)\.(jpg|jpeg|png)$"
video_regex = "https:\/\/cdn.discordapp.com\/attachments\/[0-9]*\/[0-9]*\/([a-zA-Z0-9\_\-\.]*)\.(mp4|avi|mov)$"


def isImage(content):
    result = re.match(image_regex, str(content).lower())
    return result.group(2) if result else None


def isVideo(content):
    result = re.match(video_regex, str(content).lower())
    return result.group(2) if result else None


def safeString(text):
    return "".join(
        char for char in str(text) if char.isalnum() or char in ["-", "_", "."]
    )


def formatDate(dt):
    return dt.strftime("%Y-%m-%d_%H-%M-%S")


def createFolder(server_name, channel_name):
    myDateTime = formatDate(datetime.now())
    folder = f"{os.getcwd()}\\{safeString(server_name)}_{safeString(channel_name)}_{myDateTime}\\"
    os.mkdir(folder)
    return folder


def downloadMedia(url, folder, file_name):
    with open(folder + file_name, "wb") as file:
        response = get(url)
        file.write(response.content)


def bytes_to_mb(byte):
    return round(byte / 1024 / 1024, 2)


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message):
        prefix = "`"

        if message.content[: len(prefix)] == prefix:
            command = message.content[len(prefix) :]

            if command == "ping":
                m = f"Latency: {round(self.latency * 1000, 2)}ms"
                await message.channel.send(m)
                print(m)

            elif command.startswith("info"):
                limit = (  # number of last sent messages
                    int(command.split()[1])
                    if len(command.split()) > 1 and command.split()[1].isdigit()
                    else 5  # default: check last 5 messages.
                )

                message_history = await message.channel.history(limit=limit).flatten()

                print(f"\n{formatDate(datetime.now())}\n{'_' * 20}\n")

                images, videos, others = {}, {}, {}
                total_image_size, total_video_size, total_other_size = 0, 0, 0

                counter = 1
                for m in message_history:
                    if m.attachments:
                        print(f"{counter} - {m.author.name}: {m.attachments[0]}")

                        if isImage(m.attachments[0]):
                            print(f"image {bytes_to_mb(m.attachments[0].size)}mb")
                            total_image_size += m.attachments[0].size
                            images[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(message.created_at),
                                safeString(str(message.author)),
                                str(m.attachments[0]).split(".")[-1],
                            )
                        elif isVideo(m.attachments[0]):
                            print(f"video {bytes_to_mb(m.attachments[0].size)}mb")
                            total_video_size += m.attachments[0].size
                            videos[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(message.created_at),
                                safeString(str(message.author)),
                                str(m.attachments[0]).split(".")[-1],
                            )
                        else:
                            total_other_size += m.attachments[0].size
                            oth_ext = str(m.attachments[0]).split(".")[-1]
                            print(oth_ext)
                            others[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(message.created_at),
                                safeString(str(message.author)),
                                oth_ext,
                            )

                        counter += 1

                # Summary report message
                print("Images:", images, " Size:", total_image_size)
                print("Videos:", videos, " Size:", total_video_size)
                print("Others:", others, " Size:", total_other_size)

                colors = [0xFF0000, 0xFFEE00, 0x40FF00, 0x00BBFF, 0xFF00BB]

                embedVar = discord.Embed(title="Report", color=random.choice(colors))
                embedVar.add_field(
                    name="Messages",
                    value=f"{len(message_history)} messages found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Images",
                    value=f"{len(images)} images found. (Size: {bytes_to_mb(total_image_size)}mb)"
                    if total_image_size > 0
                    else "No image found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Videos",
                    value=f"{len(videos)} videos found. (Size: {bytes_to_mb(total_video_size)}mb)"
                    if total_video_size > 0
                    else "No video found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Total Size of Medias (Image/Video)",
                    value=f"{bytes_to_mb((total_image_size + total_video_size))}mb",
                    inline=False,
                )
                await message.channel.send(embed=embedVar)

                # Options (Images, Videos, All) message
                emojis = ["1️⃣", "2️⃣", "3️⃣"]
                options = []

                if total_image_size > 0:
                    options.append("Images")
                if total_video_size > 0:
                    options.append("Videos")
                if len(options) == 2:
                    options.append("All")

                if options:
                    options_text = "__**Download Options**__"
                    for option in options:
                        options_text += f"\n[{options.index(option) + 1}] {option}"

                    options_message = await message.channel.send(options_text)

                    # Reactions for options
                    for i in range(len(options)):
                        await options_message.add_reaction(emojis[i])

                    def check(reaction, user):
                        # Check if the user is a command author.
                        # Accept only emojis that the bot reacted.
                        # For example, if the bot reacted only '1️⃣' emoji, then the bot accept only '1️⃣' emoji.
                        return user == message.author and str(reaction.emoji) in [
                            emojis[i] for i in range(len(options))
                        ]

                    # The bot waits for the author to choose option.
                    try:
                        reaction, user = await client.wait_for(
                            "reaction_add", timeout=15.0, check=check
                        )
                    except asyncio.TimeoutError:
                        await options_message.delete()
                    else:
                        await options_message.delete()

                        selection = options[emojis.index(str(reaction))]
                        status_message = await message.channel.send(
                            f"Downloading {selection}..."
                        )

                        # Download Medias
                        folder = createFolder(message.guild.name, message.channel.name)

                        try:
                            if selection == "Images":
                                for url, name in images.items():
                                    downloadMedia(url, folder, name)
                            elif selection == "Videos":
                                for url, name in videos.items():
                                    downloadMedia(url, folder, name)
                            elif selection == "All":
                                for url, name in images.items():
                                    downloadMedia(url, folder, name)
                                for url, name in videos.items():
                                    downloadMedia(url, folder, name)
                            else:
                                print("An error occurred on selection!")

                        except Exception as ex:
                            print(ex)
                            await status_message.edit(
                                content="Something went wrong!", delete_after=10
                            )
                            return 0
                        await status_message.edit(
                            content="Download Completed.", delete_after=10
                        )


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = MyClient()
client.run(TOKEN)
