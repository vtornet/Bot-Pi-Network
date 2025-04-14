import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import time

BOT_TOKEN = "8109364952:AAFTXz1BfcrIwq2aq18QjRcmqb_m0SUDaos"

LIMITE_DIARIO = 3
DURACION_SILENCIO = 60  # minutos

multimedia_usuarios = {}
advertencias_usuarios = {}

palabras_prohibidas = [
    "idiota", "imbécil", "estúpido", "tonto", "mierda",
    "puta", "puto", "gilipollas", "maldito", "cabrón",
    "cabrona", "pendejo", "pendeja", "coño", "joder",
    "carajo", "culero", "pelotudo", "verga", "polla",
    "chingar", "chingada", "maricón", "zorra", "subnormal",
    "chupapito", "chupapitos", "mamahuevos", "mamaguevo", "mamaguevos",
    "chupa pitos", "chupa pito", "mama huevos", "mama huevo", "orto", "ano",
    "rozame el ano"
]

def escape_markdown(text: str) -> str:
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text or "")

def obtener_nombre_usuario(user):
    return escape_markdown(user.first_name or f"@{user.username}" or "Usuario")

async def redes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /redes para mostrar las redes sociales del grupo.
    """
    redes_sociales = (
        "🌐 *Redes Sociales del Grupo:*\n\n"
        "📢 *Telegram:* [Pi Network España](https://t.me/PInetworEsp)\n"
        "📸 *Instagram:* [pinetwork_social_esp](https://www.instagram.com/pinetwork_social_esp)\n"
        "🐦 *X:* [pisocialesp](https://www.x.com/pisocialesp)\n"
        "▶️ *YouTube:* [Pi Network Social ESP](https://www.youtube.com/@PiNetworkSocialESP)\n"
        "🎵 *TikTok:* [pinetworksocial](https://www.tiktok.com/@_pinetworksocial)\n"
        "🌐 *Web:* [Pi Network Social](https://www.pinetworksocial.com/)\n"
    )

    await update.message.reply_text(
        redes_sociales,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )

async def noticias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /noticias para mostrar los enlaces de noticias.
    """
    mensaje = (
        "📰 *Noticias Disponibles:*\n\n"
        "• [Core Team](https://www.pinetworksocial.com/pi-network/actualizaciones-del-core-team)\n"
        "• [Otras noticias](https://www.pinetworksocial.com/noticias)\n"
    )

    await update.message.reply_text(
        mensaje,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )

async def detectar_malas_palabras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    hoy = datetime.utcnow().date()
    texto = update.message.text.lower()
    nombre = obtener_nombre_usuario(user)

    print(f"[DEBUG] Mensaje recibido de {nombre}: {texto}")

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        print("[DEBUG] Usuario es administrador. No se aplican restricciones.")
        return

    if chat_id not in advertencias_usuarios:
        advertencias_usuarios[chat_id] = {}

    if user_id not in advertencias_usuarios[chat_id] or advertencias_usuarios[chat_id][user_id]["fecha"] != hoy:
        advertencias_usuarios[chat_id][user_id] = {"fecha": hoy, "conteo": 0}

    advertencias = advertencias_usuarios[chat_id][user_id]["conteo"]

    if advertencias >= 3:
        print(f"[DEBUG] Usuario {nombre} ya fue silenciado anteriormente.")
        return  # Ya fue silenciado

    conteo_palabras_prohibidas = sum(1 for p in palabras_prohibidas if p in texto)
    print(f"[DEBUG] Palabras prohibidas detectadas: {conteo_palabras_prohibidas}")

    if conteo_palabras_prohibidas > 0:
        advertencias += conteo_palabras_prohibidas
        advertencias_usuarios[chat_id][user_id]["conteo"] = advertencias

        try:
            await update.message.delete()
            print(f"[DEBUG] Mensaje ofensivo de {nombre} eliminado.")
        except Exception as e:
            print(f"[ERROR] No se pudo borrar mensaje ofensivo: {e}")

        await context.bot.send_message(
            chat_id,
            f"⚠️ *{nombre}*, advertencia {advertencias}/3\\.",
            parse_mode="MarkdownV2"
        )
        print(f"[DEBUG] Advertencia {advertencias}/3 enviada a {nombre}.")

        if advertencias >= 3:
            try:
                await context.bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False
                    ),
                    until_date=int(time.time()) + DURACION_SILENCIO * 60
                )
                await context.bot.send_message(
                    chat_id,
                    f"🔇 *{nombre}* ha sido silenciado por {DURACION_SILENCIO} minutos\\.",
                    parse_mode="MarkdownV2"
                )
                print(f"[DEBUG] Usuario {nombre} silenciado por {DURACION_SILENCIO} minutos.")
            except Exception as e:
                print(f"[ERROR] Error al silenciar usuario {nombre}: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("redes", redes))
    app.add_handler(CommandHandler("noticias", noticias))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), detectar_malas_palabras))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        print(f"[ERROR] {context.error}")
    app.add_error_handler(error_handler)

    print("🤖 Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()
