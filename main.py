import os
import requests
from dotenv import load_dotenv
from gofile import uploadFile
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

load_dotenv()

Bot = Client(
    "GoFile-Bot",
    bot_token=os.getenv("BOT_TOKEN"),
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH")
)

INSTRUCTIONS = """
I am a gofile uploader telegram bot.
You can upload files to gofile.io with command.

With media:
    Normal:
        `/upload`
    With token:
        `/upload token`
    With folder id:
        `/upload token folderid`

Using Link:
    Normal:
        `/upload url`
    With token:
        `/upload url token`
    With folder id:
        `/upload url token folderid`
"""

@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    await update.reply_text(
        text=f"Hello {update.from_user.mention}," + INSTRUCTIONS,
        disable_web_page_preview=True,
        quote=True
    )

@Bot.on_message(filters.private & filters.command("upload"))
async def upload(bot, update):
    message = await update.reply_text(
        text="`Processing...`",
        quote=True,
        disable_web_page_preview=True
    )

    text = update.text.split(maxsplit=1)[1] if len(update.text.split()) > 1 else None
    url = token = folderId = None

    if text:
        if text.startswith("http://") or text.startswith("https://"):
            url, *params = text.split()
            if params:
                token = params[0] if len(params) >= 1 else None
                folderId = params[1] if len(params) >= 2 else None
        else:
            token, folderId = text.split(maxsplit=1)

    try:
        await message.edit_text("`Downloading...`")
        if url:
            response = requests.get(url)
            media = response.url.split("/")[-1]
            with open(media, "wb") as file:
                file.write(response.content)
        else:
            media = await update.reply_to_message.download()
        await message.edit_text("`Downloaded Successfully`")

        await message.edit_text("`Uploading...`")
        response = uploadFile(file=media, token=token, folderId=folderId)
        await message.edit_text("`Uploaded Successfully`")

        try:
            os.remove(media)
        except Exception as e:
            print(f"Failed to delete {media}: {e}")

        text = f"**File Name:** `{response['fileName']}`\n"
        text += f"**File ID:** `{response['fileId']}`\n"
        text += f"**Code:** `{response['code']}`\n"
        text += f"**md5:** `{response['md5']}`\n"
        text += f"**Download Page:** `{response['downloadPage']}`"

        link = response['downloadPage']
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Open Link", url=link),
                    InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url={link}")
                ],
                [
                    InlineKeyboardButton(text="Feedback", url="https://telegram.me/FayasNoushad")
                ]
            ]
        )
        await message.edit_text(
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    except Exception as e:
        await message.edit_text(f"Error: {e}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    Bot.start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    Bot.idle()
    Bot.stop()
