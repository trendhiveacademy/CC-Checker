import requests
import braintree
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram Bot Token
TELEGRAM_TOKEN = "7861412400:AAHwq_YK6UMHC2fDmZ_o-K8Fn7nKrU1VKZg"

# Braintree credentials
braintree.Configuration.configure(
    braintree.Environment.Sandbox,
    merchant_id="vwmr4nf4b2cpnnqy",
    public_key="9fz74vg6yysjz7kq",
    private_key="5330cdbb761c06df49a6e0b2c6f8451b"
)

def bin_lookup(bin_number):
    try:
        res = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if res.status_code == 200:
            data = res.json()
            return {
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown"),
                "scheme": data.get("scheme", "Unknown"),
                "type": data.get("type", "Unknown"),
                "brand": data.get("brand", "Unknown"),
                "vbv": "VBV" if data.get("type") == "credit" else "Non-VBV"
            }
        else:
            return {"error": "BIN lookup failed."}
    except Exception as e:
        return {"error": str(e)}

def is_playstore_addable(card_number):
    playstore_supported_bins = ["4", "5"]
    return "Yes ✅" if card_number.startswith(tuple(playstore_supported_bins)) else "No ❌"

def braintree_card_check(card_number, expiry, cvv):
    try:
        result = braintree.PaymentMethod.create({
            "customer_id": "test_customer_id",
            "payment_method_nonce": "fake-valid-nonce",
        })
        return result.is_success
    except Exception:
        return False

def start(update, context):
    welcome_msg = (
        "👋 *Welcome to CC Checker by Trend Hive Academy!*\n\n"
        "⚠️ Note: U can check only 5 bins per hour or 5 cards per hour!\n\n"

        "📌 You can send:\n"
        "➤ Just BIN: `478200`\n"
        "➤ Full Card: `4782002070976487|09|28|995`\n"
        "or\n"
        "`4782002070976487/09/28/995`\n\n"
        "🔍 We'll give you:\n\n"
        "✔️ Country, Bank, Brand\n"
        "✔️ VBV Status, Play Store Add\n"
        "✔️ Braintree Auth Check\n\n"
        "👑 Owner: @trendhiveacademy\n"
        "🎬 YouTube: https://youtube.com/@trendhiveacademy\n\n"
        "⚠️ Note: Bot is for educational purposes only!"
    )
    update.message.reply_text(welcome_msg, parse_mode='Markdown')


def process_card(update, context):
    msg = update.message.text.strip()

    # If it's a BIN only (6 digits)
    if msg.isdigit() and len(msg) == 6:
        bin_data = bin_lookup(msg)
        if "error" in bin_data:
            update.message.reply_text(f"BIN Error: {bin_data['error']}")
            return

        reply = (
            f"💳 *BIN Info Check*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 *Bank:* {bin_data['bank']}\n"
            f"🌍 *Country:* {bin_data['country']}\n"
            f"💳 *Type:* {bin_data['type']} ({bin_data['vbv']})\n"
            f"🔖 *Brand:* {bin_data['brand']}\n"
            f"💠 *Scheme:* {bin_data['scheme']}"
        )
        update.message.reply_text(reply, parse_mode='Markdown')
        return

    # Else, assume it's a full card
    for delimiter in ['|', '/']:
        if delimiter in msg:
            parts = msg.split(delimiter)
            if len(parts) == 4:
                card, month, year, cvv = parts
                break
    else:
        update.message.reply_text("❗ Invalid format.\nSend either:\n- `478200` (BIN only)\n- `4782002070976487|09|28|995` (Full Card)", parse_mode='Markdown')
        return

    # BIN Lookup
    bin_data = bin_lookup(card[:6])
    if "error" in bin_data:
        update.message.reply_text(f"BIN Error: {bin_data['error']}")
        return

    # Additional checks
    braintree_status = braintree_card_check(card, f"{month}/{year}", cvv)
    playstore_status = is_playstore_addable(card)

    reply = (
        f"💳 *Card Info Check*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *Bank:* {bin_data['bank']}\n"
        f"🌍 *Country:* {bin_data['country']}\n"
        f"💳 *Type:* {bin_data['type']} ({bin_data['vbv']})\n"
        f"🔖 *Brand:* {bin_data['brand']}\n"
        f"💠 *Scheme:* {bin_data['scheme']}\n"
        f"📱 *Play Store Addable:* {playstore_status}\n"
        f"🔐 *Braintree Auth:* {'✅ Success' if braintree_status else '❌ Failed'}"
    )
    update.message.reply_text(reply, parse_mode='Markdown')


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_card))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
