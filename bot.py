from datetime import datetime, timedelta
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

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        nombre = obtener_nombre_usuario(new_member)
        await update.message.reply_text(
            f"¡Bienvenid@ *{nombre}* al grupo oficial de *Pi Network* 🚀\!\n\n"
            "*Normas del grupo:*\n"
            "• *Respeto a todos:* Sin insultos ni conflictos.\n"
            "• *No spam:* Evita mensajes repetitivos o publicidad.\n"
            "• *Contenido adecuado:* Mantén el tema sobre Pi Network.\n"
            f"• *Límite multimedia:* Máximo {LIMITE_DIARIO} archivos por día.\n\n"
            "Escribe /ayuda para ver los comandos disponibles.",
            parse_mode="MarkdownV2"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ayuda(update, context)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Comandos disponibles:*\n"
        "/start \\- Mensaje de bienvenida\n"
        "/ayuda \\- Muestra esta ayuda\n"
        "/multimedia \\- Ver tus envíos hoy\n"
        "/reportar [motivo] \\- Reporta a otro usuario\n\n"
        "⚠️ Evita lenguaje ofensivo\\.",
        parse_mode="MarkdownV2"
    )

async def reportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] Comando /reportar recibido")

    user = update.effective_user
    nombre = obtener_nombre_usuario(user)

    motivo_raw = " ".join(context.args).strip() if context.args else "Motivo no especificado"
    motivo = escape_markdown(motivo_raw)

    menciones_admins = "@Kekomst @Alex_Alves87 @Gabrielacsk @Magic2013"

    await update.message.reply_text(
        f"📣 *{nombre}* ha enviado un reporte\\.\n"
        f"*Motivo:* {motivo}\n"
        f"Los administradores han sido notificados: {menciones_admins}",
        parse_mode="MarkdownV2"
    )



async def controlar_envio_multimedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    hoy = datetime.utcnow().date()

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        return

    if chat_id not in multimedia_usuarios:
        multimedia_usuarios[chat_id] = {}

    if user_id not in multimedia_usuarios[chat_id] or multimedia_usuarios[chat_id][user_id]["fecha"] != hoy:
        multimedia_usuarios[chat_id][user_id] = {"fecha": hoy, "conteo": 0}

    if multimedia_usuarios[chat_id][user_id]["conteo"] >= LIMITE_DIARIO:
        try:
            await update.message.delete()
        except Exception as e:
            print(f"No se pudo borrar mensaje multimedia: {e}")
        nombre = obtener_nombre_usuario(user)
        await context.bot.send_message(
            chat_id,
            f"⚠️ *{nombre}*, límite de {LIMITE_DIARIO} archivos alcanzado hoy\\.",
            parse_mode="MarkdownV2"
        )
    else:
        multimedia_usuarios[chat_id][user_id]["conteo"] += 1

async def detectar_malas_palabras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    hoy = datetime.utcnow().date()
    texto = update.message.text.lower()
    nombre = obtener_nombre_usuario(user)

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        return

    if chat_id not in advertencias_usuarios:
        advertencias_usuarios[chat_id] = {}

    if user_id not in advertencias_usuarios[chat_id] or advertencias_usuarios[chat_id][user_id]["fecha"] != hoy:
        advertencias_usuarios[chat_id][user_id] = {"fecha": hoy, "conteo": 0}

    advertencias = advertencias_usuarios[chat_id][user_id]["conteo"]

    if advertencias >= 3:
        return  # Ya fue silenciado

    if any(p in texto for p in palabras_prohibidas):
        advertencias += 1
        advertencias_usuarios[chat_id][user_id]["conteo"] = advertencias

        try:
            await update.message.delete()
        except Exception as e:
            print(f"No se pudo borrar mensaje ofensivo: {e}")

        await context.bot.send_message(
            chat_id,
            f"⚠️ *{nombre}*, advertencia {advertencias}/3\\.",
            parse_mode="MarkdownV2"
        )

        if advertencias == 3:
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
            except Exception as e:
                print(f"Error al silenciar: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("reportar", reportar))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Sticker.ALL | filters.ANIMATION,
        controlar_envio_multimedia
    ))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), detectar_malas_palabras))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        print(f"[ERROR] {context.error}")
    app.add_error_handler(error_handler)

    print("🤖 Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()

