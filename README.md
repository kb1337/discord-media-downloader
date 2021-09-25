# Discord Media Downloader

A discord bot that downloads images and videos from a selected channel. You have to be the admin of the server to use this bot.

</br>

### Image extentions

> jpg, jpeg, png

### Video extentions

> mp4, avi, mov

</br>

<img width="300" src="https://user-images.githubusercontent.com/73403802/134777697-00b300fe-0cea-4d65-9d38-f4702ce7e0ce.png" />

</br>
</br>

## Installation

Install requirements for the bot.

```sh
pip install -r .\requirements.txt
```

## Setup Bot

1- You need to create discord application in here https://discord.com/developers/applications

2- Under `Bot` tab, add bot.

3- You can use this link for add bot to your server. Simply copy your Client ID in `OAuth2` tab and paste it into `YOUR_CLIENT_ID`

---

`https://discord.com/api/oauth2/authorize?client_id=`YOUR_CLIENT_ID`&permissions=68672&scope=bot`

---

OR

You can munually select permisions.

In `OAuth2` tab, select `bot` for Scopes. Then, add bot permissions below.

- View Channels
- Send Messages
- Read Message History
- Add Reactions

</br>

4- Create a file named `.env` in the root folder of your project.

</br>

<img width="80%" src="https://user-images.githubusercontent.com/73403802/134777401-56463274-8f23-4988-a82e-4a7b1b9419e7.png" />

</br>
</br>

5- Copy your bot's TOKEN and save it in the `.env` file as shown below. (without quotes)

```
DISCORD_TOKEN=YOUR_TOKEN
```

</br>

## Usage

You can change the [prefix](https://github.com/kb1337/Discord-Media-Downloader/blob/8d71aeb105a5c6e50468c8f54b361dc97faba040/bot.py#L125). Default prefix:

> <strong>`</strong>

### Bot Commands

```python
`ping # Return bot's latency
```

```python
`info <limit> # Returns stats about messages and download options (default limit 5) (administrator permission needed)
```

## License

[MIT](https://github.com/kb1337/Discord-Media-Downloader/blob/master/LICENSE)
