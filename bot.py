import discord, logging, os, re, asyncio, random
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


image_regex = "https:\/\/cdn.discordapp.com\/attachments\/[0-9]*\/[0-9]*\/([a-z0-9\_\-\.]*)\.(jpg|jpeg|png)$"
video_regex = "https:\/\/cdn.discordapp.com\/attachments\/[0-9]*\/[0-9]*\/([a-z0-9\_\-\.]*)\.(mp4|avi|mov)$"


def isImage(content):
    return True if re.match(image_regex, str(content).lower()) else False


def isVideo(content):
    return True if re.match(video_regex, str(content).lower()) else False


def safeString(text):
    return "".join(
        char for char in str(text) if char.isalnum() or char in ["-", "_", "."]
    )


def formatDate(dt):
    return dt.strftime("%Y-%m-%d_%H-%M-%S")


def createFolder(server_name, channel_name):
    folder = "{}\\{}_{}_{}\\".format(
        os.getcwd(),
        safeString(server_name),
        safeString(channel_name),
        formatDate(datetime.now()),
    )
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder


async def downloadMedia(url, folder, file_name):
    print(f"\nDownloading {url} as {file_name}")
    with open(folder + file_name, "wb") as file:
        response = get(url)
        file.write(response.content)
    print(f"Download Successfull. {file_name}")


def bytes_to_mb(byte):
    return round(byte / 1024 / 1024, 3)


async def reactForDownload(
    command_message,
    options,
    options_message,
    options_emojis,
    images,
    videos,
    others,
):
    # Check if the user is a command author.
    # Accept only emojis that the bot reacted.
    # For example, if the bot reacted only '1️⃣' emoji, then the bot accept only '1️⃣' emoji.
    def check(reaction, user):
        return (
            reaction.message.id == options_message.id
            and user == command_message.author
            and str(reaction.emoji) in options_emojis
        )

    # The bot waits for the author to choose option.
    try:
        reaction, r_user = await client.wait_for(
            "reaction_add", timeout=15.0, check=check
        )
    except asyncio.TimeoutError:
        await options_message.delete()
    else:
        # After author choose option
        await options_message.delete()
        selection = options[options_emojis.index(str(reaction))]
        status_message = await command_message.channel.send(
            f"Downloading {selection}..."
        )

        # Download Medias
        folder = createFolder(command_message.guild.name, command_message.channel.name)

        try:
            if selection == "Images":
                for url, name in images.items():
                    await downloadMedia(url, folder, name)
            elif selection == "Videos":
                for url, name in videos.items():
                    await downloadMedia(url, folder, name)
            elif selection == "All":
                for url, name in images.items():
                    await downloadMedia(url, folder, name)
                for url, name in videos.items():
                    await downloadMedia(url, folder, name)
            else:
                print("An error occurred on selection!")

        except Exception as ex:
            print(ex)
            await status_message.edit(content="Something went wrong!", delete_after=10)
            return 0
        await status_message.edit(content="Download Completed.", delete_after=10)


class MyClient(discord.Client):
    async def on_ready(self):
        print("{0} is ALIVE!".format(self.user.name))

    async def on_message(self, message):
        self.prefix = "`"

        if message.content[: len(self.prefix)] == self.prefix:
            self.command = message.content[len(self.prefix) :]
            self.isAdmin = message.author.guild_permissions.administrator

            if message.author.bot:
                print("Robots can not give me orders!")
                return 0

            print(
                f"\n{formatDate(datetime.now())}:{str(message.author)}:{self.command}\n{'_' * 40}\n"
            )

            if self.command == "ping":
                m = f"Latency: {round(self.latency * 1000, 2)}ms"
                await message.channel.send(m)
                print(m)

            elif self.command.startswith("info"):
                if not self.isAdmin:
                    await message.reply("This is admin only command.", delete_after=10)
                    print("Unauthorized")
                    return 0

                self.limit = (  # number of messages (newest to oldest)
                    int(self.command.split()[1])
                    if len(self.command.split()) > 1
                    and self.command.split()[1].isdigit()
                    else 5  # default: check last 5 messages.
                )

                self.message_history = await message.channel.history(
                    limit=self.limit
                ).flatten()

                self.images, self.videos, self.others = {}, {}, {}
                self.total_image_size, self.total_video_size, self.total_other_size = (
                    0,
                    0,
                    0,
                )

                self.counter = 1
                for m in self.message_history:
                    if m.attachments and not m.author.bot:
                        print(f"{self.counter} - {m.author.name}: {m.attachments[0]}")

                        if isImage(m.attachments[0]):
                            print(f"image {bytes_to_mb(m.attachments[0].size)}mb")

                            self.total_image_size += m.attachments[0].size
                            self.images[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(m.created_at),
                                safeString(str(m.author)),
                                str(m.attachments[0]).split(".")[-1],
                            )
                        elif isVideo(m.attachments[0]):
                            print(f"video {bytes_to_mb(m.attachments[0].size)}mb")

                            self.total_video_size += m.attachments[0].size
                            self.videos[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(m.created_at),
                                safeString(str(m.author)),
                                str(m.attachments[0]).split(".")[-1],
                            )
                        else:
                            print(f"other {bytes_to_mb(m.attachments[0].size)}mb")
                            self.total_other_size += m.attachments[0].size
                            self.others[str(m.attachments[0])] = "{}_{}.{}".format(
                                formatDate(m.created_at),
                                safeString(str(m.author)),
                                str(m.attachments[0]).split(".")[-1],
                            )

                        self.counter += 1

                # Summary report message
                colors = [0xFF0000, 0xFFEE00, 0x40FF00, 0x00BBFF, 0xFF00BB]

                embedVar = discord.Embed(title="Report", color=random.choice(colors))
                embedVar.add_field(
                    name="Messages",
                    value=f"{len(self.message_history)} messages found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Images",
                    value=f"{len(self.images)} images found. (Size: {bytes_to_mb(self.total_image_size)}mb)"
                    if self.total_image_size > 0
                    else "No image found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Videos",
                    value=f"{len(self.videos)} videos found. (Size: {bytes_to_mb(self.total_video_size)}mb)"
                    if self.total_video_size > 0
                    else "No video found.",
                    inline=False,
                )
                embedVar.add_field(
                    name="Total Size of Medias (Image/Video)",
                    value=f"{bytes_to_mb((self.total_image_size + self.total_video_size))}mb",
                    inline=False,
                )
                await message.channel.send(embed=embedVar)

                # Options (Images, Videos, All) message
                emojis = ["1️⃣", "2️⃣", "3️⃣"]
                self.options = []

                if self.total_image_size > 0:
                    self.options.append("Images")
                if self.total_video_size > 0:
                    self.options.append("Videos")
                if len(self.options) == 2:
                    self.options.append("All")

                if self.options:
                    self.options_text = "__**Download Options**__"
                    for option in self.options:
                        self.options_text += (
                            f"\n[{self.options.index(option) + 1}] {option}"
                        )

                    self.options_message = await message.channel.send(self.options_text)

                    # Reactions for options
                    for i in range(len(self.options)):
                        await self.options_message.add_reaction(emojis[i])

                    self.options_emojis = [emojis[i] for i in range(len(self.options))]

                    # Handles multiple commands at the same time.
                    await reactForDownload(
                        message,
                        self.options,
                        self.options_message,
                        self.options_emojis,
                        self.images,
                        self.videos,
                        self.others,
                    )
            else:
                print("Unknown command")


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = MyClient()
client.run(TOKEN)
