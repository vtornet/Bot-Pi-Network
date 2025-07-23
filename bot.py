import os
import re
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from bs4 import BeautifulSoup
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from datetime import datetime, timedelta, timezone
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "TU_BOT_TOKEN_AQUI")
LIMITE_DIARIO = 5
DURACION_SILENCIO = 60  # minutos

multimedia_usuarios = {}
ultima_consulta_precio = {"hora": None, "mensaje_id": None, "chat_id": None}

palabras_prohibidas = [
    "idiota", "imbécil", 
    "puta", "puto", "gilipollas", "maldito", "cabrón",
    "cabrona", "pendejo", "pendeja", "coño", "joder",
    "carajo", "culero", "pelotudo", "verga", "polla", "pollas",
    "chingar", "chingada", "maricón", "zorra", "subnormal",
    "chupapito", "chupapitos", "mamahuevos", "mamaguevo", "mamaguevos",
    "chupa pitos", "chupa pito", "mama huevos", "mama huevo", 
    "rozame el ano", "cabron", "imbecil",  
    "gilí", "pringado", "capullo", "soplapollas", "tontolaba",
    "meapilas", "mindundi", "caraculo", "comemierda", "toca huevos",
    "pinche", "naco", "güey", "pendejazo", "mamón",
    "cagón", "traga mierda", "chupamedias", 
    "boludo", "pelotudo", "mogólico", "forro", "conchudo",
    "bobo", "chupaculo", "cabeza de termo",
    "weón", "culiao", "saco wea", "conchesumadre", "maraco",
    "picao a la araña", "longi",
    "huevón", "gonorrea", "carechimba", "careverga", "marrano",
    "malparido", "zarrapastroso", "@criptosenals", "criptosenals",
    "mamagüevo", "pajuo", "mardito", "mariquito", "carapicha",
    "jalabolas", "perolito", "chúpame", "chupame",
    "cojudo", "huevón", "pavo", "chibolo de mierda", "conchatumare",
    "mamaguevo", "pariguayo", "bocón", "chopo", "lambón",
    "bellaco", "mamabicho", "pendejete", "cafre", "come mierda",
    "singao", "comemierda", "fajao", "descarao", "chivatón",
    "caremondá", "careculo", "carapinga", "caraverga", "verguero",
    "mierdero", "tarado", "imbécilazo", "estúpido de mierda", "merluzo"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = obtener_nombre_usuario(update.effective_user)
    mensaje = escape_markdown(f"¡Hola {nombre}! Usa /ayuda para ver lo que puedo hacer por ti.")
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2")

def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in text or "")

def obtener_nombre_usuario(user):
    return escape_markdown(user.first_name or f"@{user.username}" or "Usuario")

async def redes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🌐 *Redes Sociales del Grupo:*\n\n"
        "📢 *Telegram:* [Pi Network España](https://t.me/PInetworEsp)\n"
        "📸 *Instagram:* [pinetwork_social_esp](https://www.instagram.com/pinetwork_social_esp)\n"
        "🐦 *X:* [pisocialesp](https://www.x.com/pisocialesp)\n"
        "▶️ *YouTube:* [Pi Network Social ESP](https://www.youtube.com/@PiNetworkSocialESP)\n"
        "🎵 *TikTok:* [pinetworksocial](https://www.tiktok.com/@_pinetworksocial)\n"
        "🌐 *Web:* [Pi Network Social](https://www.pinetworksocial.com/)\n"
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2", disable_web_page_preview=True)

async def noticias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "📰 *Noticias Disponibles:*\n\n"
        "• [Core Team](https://www.pinetworksocial.com/pi-network/actualizaciones-del-core-team)\n"
        "• [Otras noticias](https://www.pinetworksocial.com/noticias)\n"
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2", disable_web_page_preview=True)

async def reportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    nombre = obtener_nombre_usuario(user)
    motivo_raw = " ".join(context.args).strip() if context.args else "Motivo no especificado"
    motivo = escape_markdown(motivo_raw)
    menciones_admins = escape_markdown("@Kekomst @Alex_Alves87 @Galleguu @Gabrielacsk @Magic2013")

    await update.message.reply_text(
        f"📣 *{nombre}* ha enviado un reporte\\.\n"
        f"*Motivo:* {motivo}\n"
        f"Los administradores han sido notificados: {menciones_admins}",
        parse_mode="MarkdownV2"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = escape_markdown(
        "ℹ️ Lista de Comandos Disponibles:\n\n"
        "/redes - Muestra las redes sociales del grupo.\n"
        "/noticias - Muestra noticias relacionadas con Pi Network.\n"
        "/reportar <motivo> - Envía un reporte a los administradores.\n"
        "/multimedia - Consulta los archivos multimedia que puedes enviar hoy.\n"
        "/ayuda - Muestra esta lista de comandos.\n"
        "/donaciones - Cómo apoyar al grupo con una donación.\n"
        "/referido - Enlace con beneficios de Bitget.\n"
        "/precio - Muestra el precio actual de Pi."
        "/kyc - Muestra enlace a tutorial de KYC."
    )
    await update.message.reply_text(comandos, parse_mode="MarkdownV2")

from telegram.constants import ParseMode

async def kyc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🔍 *Consulta sobre KYC:*\n\n"
        "Se recomienda visitar el siguiente tutorial para resolver dudas comunes sobre el proceso de KYC:\n"
        "[Tutorial de KYC](https://www\\.pinetworksocial\\.com/pi\\-network/tutorial\\-kyc/)\n\n"
        "No obstante, si aún tienes problemas o preguntas, puedes hacer tu consulta en el grupo libremente\\."
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2", disable_web_page_preview=True)
       
async def multimedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    hoy = datetime.now(timezone.utc).date()

    if chat_id not in multimedia_usuarios:
        multimedia_usuarios[chat_id] = {}

    if user_id not in multimedia_usuarios[chat_id] or multimedia_usuarios[chat_id][user_id]["fecha"] != hoy:
        multimedia_usuarios[chat_id][user_id] = {"fecha": hoy, "conteo": 0}

    conteo = multimedia_usuarios[chat_id][user_id]["conteo"]
    restante = max(0, LIMITE_DIARIO - conteo)

    mensaje = escape_markdown(
        f"📷 Multimedia Disponible:\n\n"
        f"Has enviado {conteo} de {LIMITE_DIARIO} archivos multimedia hoy.\n"
        f"Te quedan {restante} archivos por enviar."
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2")

async def controlar_envio_multimedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    hoy = datetime.now(timezone.utc).date()

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        return

    if chat_id not in multimedia_usuarios:
        multimedia_usuarios[chat_id] = {}

    if user_id not in multimedia_usuarios[chat_id] or multimedia_usuarios[chat_id][user_id]["fecha"] != hoy:
        multimedia_usuarios[chat_id][user_id] = {"fecha": hoy, "conteo": 0}

    conteo_actual = multimedia_usuarios[chat_id][user_id]["conteo"]

    if conteo_actual >= LIMITE_DIARIO:
        try:
            await update.message.delete()
        except Exception as e:
            print(f"[ERROR] No se pudo borrar multimedia extra: {e}")

        nombre = obtener_nombre_usuario(user)
        await context.bot.send_message(
            chat_id,
            f"⚠️ *{nombre}*, ya has alcanzado el límite de {LIMITE_DIARIO} archivos multimedia hoy\\.",
            parse_mode="MarkdownV2"
        )
    else:
        multimedia_usuarios[chat_id][user_id]["conteo"] += 1

async def dar_bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        nombre = obtener_nombre_usuario(member)
        mensaje = escape_markdown(
            f"¡Bienvenid@ {nombre} al grupo Pi Network Social Esp 🚀!\n\n"
            "Normas del grupo:\n"
            "• Respeto a todos: Sin insultos ni conflictos.\n"
            "• No spam: Evita mensajes repetitivos o publicidad.\n"
            "• Contenido adecuado: El grupo está dividido en temas, el contenido debe estar relacionado con el título.\n"
            "• Límite multimedia: Máximo 5 archivos por día.\n\n"
            "Escribe /ayuda para ver los comandos disponibles."
            "Por el bien del grupo, usa el bot con moderación."
        )
        await update.message.reply_text(mensaje, parse_mode="MarkdownV2")

async def referido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🔗 *Enlace de Referido:*\n\n"
        "Este es el enlace de referido en Bitget de *Pi Network Social Esp*:\n"
        "[https://partner\\.bitget\\.com/bg/TBJXL6](https://partner.bitget.com/bg/TBJXL6)\n\n"
        "Si te unes con nuestro código de afiliado tendrás *descuentos y reembolsos* en las comisiones de transacción de *Spot*\\. 💰"
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2", disable_web_page_preview=False)

async def donaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = escape_markdown(
        "💖 *Apoya nuestro grupo:*\n"
        "Puedes contribuir al mantenimiento y desarrollo del grupo realizando una donación.\n\n"
        "🌐 *Billetera de Bitget para transferir Pi:*\n"
        "MDFNWH6ZFJVHJDLBMNOUT35X4EEKQVJAO3ZDL4NL7VQJLC4PJOQFWAAAAAAQASLTL7QXC\n\n"
        "📧 *Contacto para soporte:* www.pinetworksocial.com/contacto\n\n"
        "¡Gracias por tu apoyo! 🚀"
    )
    await update.message.reply_text(mensaje, parse_mode="MarkdownV2")

async def detectar_malas_palabras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    texto = update.message.text.lower()
    nombre = obtener_nombre_usuario(user)

    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        return

    if any(p in texto for p in palabras_prohibidas):
        try:
            await update.message.delete()
        except Exception as e:
            print(f"[ERROR] No se pudo borrar mensaje ofensivo: {e}")

        await context.bot.send_message(
            chat_id,
            f"⚠️ *{nombre}*, tu mensaje fue eliminado por lenguaje ofensivo o scam\\. Por favor mantén el respeto en el grupo\\.",
            parse_mode="MarkdownV2"
        )

async def precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    
    # Verificar si el usuario es administrador
    admins = await context.bot.get_chat_administrators(chat_id)
    es_admin = user_id in [admin.user.id for admin in admins]
    
    # Si no es admin y ha pasado menos de 1 hora desde la última consulta
    if not es_admin and ultima_consulta_precio["hora"] and (datetime.now(timezone.utc) - ultima_consulta_precio["hora"]) < timedelta(hours=1):
        if ultima_consulta_precio["mensaje_id"] and ultima_consulta_precio["chat_id"] == chat_id:
            try:
                mensaje = (
                    "⚠️ *Consulta limitada*\n\n"
                    "Con el fin de evitar el uso excesivo del comando /precio\\, "
                    "sólo se puede realizar una consulta por hora\\.\n\n"
                    "Ahí puedes ver la consulta más reciente\\."
                )
                await update.message.reply_text(
                    mensaje,
                    parse_mode="MarkdownV2",
                    reply_to_message_id=ultima_consulta_precio["mensaje_id"]
                )
            except Exception as e:
                print(f"[ERROR] No se pudo redirigir al mensaje anterior: {e}")
                await update.message.reply_text(
                    "⚠️ El comando /precio solo puede usarse una vez por hora\\. La última consulta fue hace menos de una hora\\.",
                    parse_mode="MarkdownV2"
                )
        else:
            await update.message.reply_text(
                "⚠️ El comando /precio solo puede usarse una vez por hora\\. La última consulta fue hace menos de una hora\\.",
                parse_mode="MarkdownV2"
            )
        return
    
    url = "https://api.coingecko.com/api/v3/coins/pi-network"
    chart_url = "https://api.coingecko.com/api/v3/coins/pi-network/market_chart?vs_currency=usd&days=1"

    try:
        # Datos actuales
        data = requests.get(url).json()
        market = data["market_data"]

        price = market["current_price"]["usd"]
        market_cap = market["market_cap"]["usd"]
        volume_24h = market["total_volume"]["usd"]
        change_24h = market["price_change_percentage_24h"]
        high_24h = market["high_24h"]["usd"]
        low_24h = market["low_24h"]["usd"]
        ath = market["ath"]["usd"]
        atl = market["atl"]["usd"]
        homepage = data["links"]["homepage"][0]

        tendencia = "📈" if change_24h >= 0 else "📉"

        # Obtener datos para gráfico
        chart_data = requests.get(chart_url).json()
        prices = chart_data["prices"]
        times = [datetime.fromtimestamp(p[0] / 1000, tz=timezone.utc) for p in prices]
        values = [p[1] for p in prices]

        # Crear gráfico
        plt.figure(figsize=(8, 4))
        plt.plot(times, values, color="purple", linewidth=2)
        plt.title("PI - Últimas 24h", fontsize=14)
        plt.xlabel("Hora", fontsize=10)
        plt.ylabel("Precio (USD)", fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        mensaje = (
            "*💰 Precio de Pi Network \\(\\$PI\\)*\n\n"
            + f"• *Precio actual:* \\${escape_markdown(f'{price:,.4f}')} USD {tendencia}\n"
            + f"• *Market Cap:* \\${escape_markdown(f'{market_cap:,.0f}')} USD\n"
            + f"• *Volumen \\(24h\\):* \\${escape_markdown(f'{volume_24h:,.0f}')} USD\n"
            + f"• *Cambio 24h:* {escape_markdown(f'{change_24h:.2f}')}\\%\n"
            + f"• *Máximo 24h:* \\${escape_markdown(f'{high_24h:,.4f}')} USD\n"
            + f"• *Mínimo 24h:* \\${escape_markdown(f'{low_24h:,.4f}')} USD\n"
            + f"• *ATH:* \\${escape_markdown(f'{ath:,.4f}')} USD\n"
            + f"• *ATL:* \\${escape_markdown(f'{atl:,.4f}')} USD\n\n"
            + f"🌐 *Sitio oficial:* [{escape_markdown(homepage)}]({escape_markdown(homepage)})"
        )

        sent_message = await update.message.reply_photo(photo=buffer, caption=mensaje, parse_mode="MarkdownV2")
        
        # Actualizar la última consulta solo si no es admin
        if not es_admin:
            ultima_consulta_precio["hora"] = datetime.now(timezone.utc)
            ultima_consulta_precio["mensaje_id"] = sent_message.message_id
            ultima_consulta_precio["chat_id"] = chat_id

    except Exception as e:
        print(f"[ERROR] al obtener precio de Pi: {e}")
        await update.message.reply_text(
            escape_markdown("❌ No se pudo obtener la información de $PI en este momento. Intenta más tarde."),
            parse_mode="MarkdownV2"
        )
        
patrones_spam = [
    r"http[s]?://[^ ]*(\.cn|\.ru|binancegift|airdrops?|bonus|freecrypto)",  # dominios y enlaces sospechosos
    r"gana\s+dinero\s+r[aá]pido",  # frases comunes de scam
    r"hazte\s+rico", 
    r"multiplica\s+tu\s+inversi[oó]n",
    r"env[ií]a\s+(usdt|btc|eth)\s+a\s+esta\s+direcci[oó]n",
    r"airdrop",
    r"@criptopumpva",
    r"@criptosenals",
    r"criptosenals"
    r"@criptopummps"
    r"criptopumpva",
    r"Anyone\s+sell\s+pi"
    r"Miren\s+este\s+canal"
    r"retira\s+tu\s+bono",
    r"spotsenales",
    r"@pumpsenals",
    
]

async def detectar_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.lower()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Si es admin, ignoramos
    admins = await context.bot.get_chat_administrators(chat_id)
    if user_id in [admin.user.id for admin in admins]:
        return

    for patron in patrones_spam:
        if re.search(patron, texto):
            try:
                await update.message.delete()
            except Exception as e:
                print(f"[ERROR] No se pudo borrar mensaje sospechoso de spam/scam: {e}")
            return  # solo eliminamos, sin mensaje


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('redes', redes))
    app.add_handler(CommandHandler('noticias', noticias))
    app.add_handler(CommandHandler('reportar', reportar))
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.add_handler(CommandHandler('multimedia', multimedia))
    app.add_handler(CommandHandler('donaciones', donaciones))
    app.add_handler(CommandHandler('referido', referido))
    app.add_handler(CommandHandler('precio', precio))
    app.add_handler(CommandHandler('kyc', kyc))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, dar_bienvenida))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), detectar_malas_palabras))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), detectar_spam))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, controlar_envio_multimedia))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()
    await app.run_polling()

if __name__ == '__main__':
    import sys
    import asyncio

    async def safe_main():
        try:
            await main()
        except Exception as e:
            print(f"❌ Error al ejecutar el bot: {e}", file=sys.stderr)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.create_task(safe_main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("⛔ Bot detenido manualmente.")



































































