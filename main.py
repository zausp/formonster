
from typing import Final
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter

# Conversation states
FORM_INPUT = range(1)
VERSION = "2025.0.1"

TOKEN = os.getenv("TOKEN")
PAGE_WIDTH, PAGE_HEIGHT = A4

# ------------------ PDF FUNCTIONS ------------------ #
def overlay_5G(data, overlay_pdf, SIZE):
    print(SIZE)
    c = canvas.Canvas(overlay_pdf, pagesize=A4)
    c.setFont("Helvetica", SIZE)

    # Fill fields
    c.drawString(150, PAGE_HEIGHT - 150, data["name"])
    c.drawString(150, PAGE_HEIGHT - 177, data["id_number"])
    c.drawString(416, PAGE_HEIGHT - 177, data["address"])
    c.drawString(416, PAGE_HEIGHT - 150, data["contact"])
    c.drawString(416, PAGE_HEIGHT - 200, data["email"])
    c.drawString(375, PAGE_HEIGHT - 390, data["package"])
    c.drawString(87, PAGE_HEIGHT - 655, data["name"])
    c.drawString(87, PAGE_HEIGHT - 680, data["id_number"])
    c.save()

def merge_pdfs(base_pdf, overlay_pdf, output_pdf):
    base = PdfReader(base_pdf)
    overlay = PdfReader(overlay_pdf)
    writer = PdfWriter()

    for i in range(len(base.pages)):
        page = base.pages[i]
        if i == 0:
            page.merge_page(overlay.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# ------------------ TELEGRAM HANDLERS ------------------ #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hi! Welcome to version {VERSION} of Formonster!\n\nPlease send all the details in **one message**, each line like this:\n\n"
        "`Full Name`\n`ID Number`\n`Address`\n`Email`\n`Phone Number`\n`Package`\n\n"
        "Example:\n```\nAhmed Mohamed\nA123456\nExample Address\nahmed@example.com\n9999999\n749\n```",
        parse_mode="Markdown",
    )
    return FORM_INPUT

async def handle_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    default_font_size = 12
    text = update.message.text.strip().splitlines()
    print(text)
    if len(text) < 6:
        await update.message.reply_text(
            "⚠️ Please send **all 6 lines** in the correct order:\nName, ID, Address, Email, Phone, Package."
        )
        return FORM_INPUT

    name, identity, address, email, contact,package = [line.strip() for line in text[:6]]



    user_data = {
        "name": name,
        "id_number": identity,
        "address": address,
        "email": email,
        "contact": contact,
        "package": package,
    }

    field_len = []
    for field, value in user_data.items():
        field_len.append(len(str(value)))

    print(max(field_len))
    if max(field_len) > 26:
        default_font_size = 9
    elif max(field_len) > 23:
        default_font_size = 10
    elif max(field_len) > 20:
        default_font_size = 11

    overlay_pdf = f"overlay_{user_id}.pdf"
    output_pdf = f"filled_form_{user_id}.pdf"

    try:
        overlay_5G(user_data, overlay_pdf, default_font_size)
        merge_pdfs("AirFibre Contract_1.pdf", overlay_pdf, output_pdf)

        with open(output_pdf, "rb") as f:
            await update.message.reply_document(f, caption="✅ Here’s your filled form!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ An error occurred: {e}")

    finally:
        for file in [overlay_pdf, output_pdf]:
            if os.path.exists(file):
                os.remove(file)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Form filling cancelled.")
    return ConversationHandler.END

# ------------------ MAIN FUNCTION ------------------ #
def main():
    request = HTTPXRequest(connect_timeout=10, read_timeout=60)

    app = ApplicationBuilder().token(TOKEN).request(request).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={FORM_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_form)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except RuntimeError:

        main()
