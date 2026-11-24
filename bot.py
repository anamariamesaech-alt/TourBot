
import os
import asyncio
import unicodedata
from urllib.parse import quote_plus

from google import genai
from google.genai import types

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from predict import analizar_texto


# ==================================================
# CONFIGURACIÓN
# ==================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODELO_GEMINI = "gemini-3.8-flash"

cliente_gemini = None

if GEMINI_API_KEY:
    cliente_gemini = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ==================================================
# CATEGORÍAS Y DESTINOS
# ==================================================

DATOS = {

    "playa": {
        "nombre": "🏖️ Destinos de playa",
        "destinos": {
            "cartagena": "Cartagena",
            "santa_marta": "Santa Marta",
            "san_andres": "San Andrés"
        }
    },

    "montana": {
        "nombre": "🏔️ Destinos de montaña",
        "destinos": {
            "salento": "Salento"
        }
    },

    "naturaleza": {
        "nombre": "🌳 Destinos de naturaleza",
        "destinos": {
            "amazonas": "Amazonas"
        }
    },

    "ciudad": {
        "nombre": "🏙️ Destinos de ciudad",
        "destinos": {
            "medellin": "Medellín",
            "bogota": "Bogotá"
        }
    }
}


# ==================================================
# TEMAS DEL MENÚ
# ==================================================

TEMAS = {
    "historia": "Historia y descripción",
    "atractivos": "Atractivos turísticos",
    "gastronomia": "Gastronomía",
    "actividades": "Actividades",
    "hospedaje": "Hospedaje",
    "hoteles": "Hoteles reales recomendados",
    "transporte": "Transporte",
    "recomendaciones": "Recomendaciones"
}


# ==================================================
# NORMALIZAR TEXTO
# ==================================================

def normalizar_texto(texto):

    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


# ==================================================
# DETECTAR ERRORES DE GEMINI
# ==================================================

def es_error_cuota(error):

    mensaje = str(error).upper()

    return (
        "429" in mensaje
        or "RESOURCE_EXHAUSTED" in mensaje
        or "TOOMANYREQUESTS" in mensaje
    )


def es_error_temporal(error):

    mensaje = str(error).upper()

    return any(
        codigo in mensaje
        for codigo in [
            "503",
            "UNAVAILABLE",
            "500",
            "502",
            "504",
            "INTERNAL SERVER ERROR"
        ]
    )


# ==================================================
# CONSULTAR GEMINI CON REINTENTOS
# ==================================================

async def generar_con_reintentos(contents):

    if not cliente_gemini:

        raise Exception(
            "No está configurada la API de Gemini."
        )

    for intento in range(3):

        try:

            respuesta = await cliente_gemini.aio.models.generate_content(

                model=MODELO_GEMINI,

                contents=contents

            )

            return respuesta

        except Exception as error:

            # No reintentar si la cuota está agotada.

            if es_error_cuota(error):

                raise error

            # Reintentar únicamente errores temporales.

            if es_error_temporal(error):

                if intento < 2:

                    espera = 3 * (2 ** intento)

                    print(
                        f"Gemini está ocupado. "
                        f"Intento {intento + 2} de 3 "
                        f"en {espera} segundos..."
                    )

                    await asyncio.sleep(espera)

                    continue

            raise error


# ==================================================
# ENLACE DE BÚSQUEDA DE HOTELES
# ==================================================

def enlace_hotel(lugar):

    busqueda = quote_plus(
        f"hoteles en {lugar}"
    )

    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={busqueda}"
    )


# ==================================================
# MENÚ PRINCIPAL
# ==================================================

def teclado_principal():

    botones = [

        [
            InlineKeyboardButton(
                "🏖️ Playas",
                callback_data="cat|playa"
            ),

            InlineKeyboardButton(
                "🏔️ Montañas",
                callback_data="cat|montana"
            )
        ],

        [
            InlineKeyboardButton(
                "🌳 Naturaleza",
                callback_data="cat|naturaleza"
            ),

            InlineKeyboardButton(
                "🏙️ Ciudades",
                callback_data="cat|ciudad"
            )
        ]

    ]

    return InlineKeyboardMarkup(botones)


# ==================================================
# MENÚ DE DESTINOS
# ==================================================

def teclado_destinos(categoria):

    botones = []

    for clave, nombre in DATOS[categoria]["destinos"].items():

        botones.append([

            InlineKeyboardButton(
                nombre,
                callback_data=f"dest|{categoria}|{clave}"
            )

        ])

    botones.append([

        InlineKeyboardButton(
            "⬅️ Menú principal",
            callback_data="inicio"
        )

    ])

    return InlineKeyboardMarkup(botones)


# ==================================================
# MENÚ DE INFORMACIÓN TURÍSTICA
# ==================================================

def teclado_fotografia():

    botones = [

        [
            InlineKeyboardButton(
                "📖 Historia y descripción",
                callback_data="foto|historia"
            )
        ],

        [
            InlineKeyboardButton(
                "📍 Atractivos turísticos",
                callback_data="foto|atractivos"
            )
        ],

        [
            InlineKeyboardButton(
                "🍽️ Gastronomía",
                callback_data="foto|gastronomia"
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 Actividades",
                callback_data="foto|actividades"
            )
        ],

        [
            InlineKeyboardButton(
                "🏨 Hospedaje",
                callback_data="foto|hospedaje"
            )
        ],

        [
            InlineKeyboardButton(
                "⭐ Hoteles reales recomendados",
                callback_data="foto|hoteles"
            )
        ],

        [
            InlineKeyboardButton(
                "🚌 Transporte",
                callback_data="foto|transporte"
            )
        ],

        [
            InlineKeyboardButton(
                "💡 Recomendaciones",
                callback_data="foto|recomendaciones"
            )
        ],

        [
            InlineKeyboardButton(
                "📸 Enviar otra fotografía",
                callback_data="otra_foto"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Menú principal",
                callback_data="inicio"
            )
        ]

    ]

    return InlineKeyboardMarkup(botones)


# ==================================================
# IDENTIFICAR LUGAR EN UNA FOTOGRAFÍA
# ==================================================

async def identificar_fotografia(imagen, mime_type):

    if not cliente_gemini:

        return None, (
            "⚠️ No está configurada la clave de Gemini."
        )

    instrucciones = """
Eres TourBot Colombia, un experto en turismo colombiano.

Analiza la fotografía e intenta identificar el lugar.

Ten en cuenta:

- Puedes reconocer lugares de cualquier departamento.
- Identifica el atractivo, monumento, playa, parque o paisaje.
- Indica el municipio y departamento si es posible.
- No te limites a una lista de destinos conocidos.
- No inventes ubicaciones.
- Si no estás seguro, dilo claramente.

Responde de manera bonita, breve y amigable.

Utiliza este formato:

📍 LUGAR IDENTIFICADO:
Nombre del lugar.

🌎 UBICACIÓN:
Municipio y departamento, si se conocen.

✨ DESCRIPCIÓN:
Una explicación breve y atractiva.

🎯 SEGURIDAD DE IDENTIFICACIÓN:
Alta, media o baja.

Si no puedes reconocerlo, explica que necesitas
otra fotografía o más información.
"""

    try:

        parte_imagen = types.Part.from_bytes(
            data=imagen,
            mime_type=mime_type
        )

        respuesta = await generar_con_reintentos(
            contents=[
                instrucciones,
                parte_imagen
            ]
        )

        resultado = respuesta.text

        if not resultado:

            return None, (
                "No pude obtener una identificación "
                "de la fotografía."
            )

        texto_normalizado = normalizar_texto(resultado)

        if (
            "no puedo identificar" in texto_normalizado
            or "no es posible identificar" in texto_normalizado
        ):

            return None, resultado

        return resultado, None

    except Exception as error:

        print(
            "Error al identificar fotografía:",
            error
        )

        if es_error_cuota(error):

            return None, (
                "⚠️ ¡Hemos alcanzado el límite de uso!\n\n"
                "No puedo analizar la fotografía en este momento. "
                "Revisa la cuota de tu API de Gemini e inténtalo "
                "cuando tengas disponibilidad."
            )

        if es_error_temporal(error):

            return None, (
                "⏳ ¡Un momento!\n\n"
                "Gemini está teniendo mucha demanda y no pudo "
                "analizar tu fotografía.\n\n"
                "Espera unos minutos y vuelve a intentarlo."
            )

        return None, (
            "❌ No pude analizar la fotografía.\n\n"
            "Intenta enviarla nuevamente."
        )


# ==================================================
# CONSULTAR INFORMACIÓN TURÍSTICA
# ==================================================

async def consultar_tema(lugar, tema):

    if not cliente_gemini:

        return "⚠️ No está configurada la clave de Gemini."

    nombre_tema = TEMAS.get(tema)

    if not nombre_tema:

        return "No encontré esa opción de información."

    # ----------------------------------------------
    # HOTELES
    # ----------------------------------------------

    if tema == "hoteles":

        enlace = enlace_hotel(lugar)

        return f"""
⭐ HOTELES EN {lugar.upper()}

¡Encuentra un lugar ideal para descansar!

Consulta hoteles reales en Google Maps:

{enlace}

🏨 Allí podrás revisar:

📍 Ubicación.
⭐ Opiniones de visitantes.
📸 Fotografías.
📞 Contacto.

💡 Antes de reservar, verifica directamente
los precios y la disponibilidad con el hotel.

TourBot no inventa nombres de establecimientos
ni confirma reservas que no ha verificado.
"""

    # ----------------------------------------------
    # PROMPT CORTO Y AMIGABLE
    # ----------------------------------------------

    instrucciones = f"""
Eres TourBot Colombia, un guía turístico amable,
creativo y apasionado por los destinos colombianos.

📍 DESTINO: {lugar}

✨ TEMA SOLICITADO: {nombre_tema}

Tu tarea es ofrecer información útil a una persona
que quiere conocer o visitar este lugar.

ESTILO DE RESPUESTA:

- Escribe en español natural y amigable.
- Utiliza emojis relacionados con el turismo.
- Incluye un título atractivo.
- Usa párrafos cortos, máximo dos líneas.
- Organiza la información con listas.
- Incluye entre 3 y 5 puntos cuando sea apropiado.
- Responde aproximadamente entre 100 y 160 palabras.
- Evita repetir ideas o agregar introducciones largas.
- No utilices demasiados emojis.
- No inventes datos, precios, direcciones ni horarios.
- Si desconoces un dato, indícalo.

CONTENIDO SEGÚN EL TEMA:

HISTORIA Y DESCRIPCIÓN:
Cuenta brevemente su origen, historia, cultura
y características especiales.

ATRACTIVOS TURÍSTICOS:
Menciona entre 3 y 5 lugares interesantes para visitar
y explica brevemente qué tiene cada uno.

GASTRONOMÍA:
Presenta los platos típicos, bebidas y dulces
tradicionales de la región.

ACTIVIDADES:
Recomienda experiencias, recorridos, aventuras
y actividades culturales o naturales.

HOSPEDAJE:
Explica qué zonas son convenientes para alojarse
y qué tipos de hospedaje puede encontrar el turista.
No inventes nombres de hoteles.

TRANSPORTE:
Explica cómo llegar y cómo movilizarse en el destino.
No inventes tarifas ni horarios.

RECOMENDACIONES:
Ofrece consejos sobre clima, equipaje, seguridad,
temporadas y cuidado del medio ambiente.

IMPORTANTE:
Habla únicamente del destino indicado y del tema solicitado.
No agregues información que no sea necesaria.
Haz que la respuesta sea agradable y fácil de leer.
"""

    try:

        respuesta = await generar_con_reintentos(
            contents=instrucciones
        )

        if respuesta.text:

            return respuesta.text.strip()

        return (
            "No encontré información suficiente "
            "para este tema."
        )

    except Exception as error:

        print(
            "Error consultando información:",
            error
        )

        if es_error_cuota(error):

            return (
                "⚠️ ¡Alcanzamos el límite de consultas!\n\n"
                "Gemini no puede responder por ahora porque "
                "se agotó la cuota disponible.\n\n"
                "Inténtalo nuevamente cuando se restablezca."
            )

        if es_error_temporal(error):

            return (
                "⏳ ¡Estamos teniendo dificultades!\n\n"
                "Gemini está experimentando una alta demanda.\n\n"
                "Espera unos minutos y vuelve a intentarlo."
            )

        return (
            "❌ No pude consultar la información en este momento.\n\n"
            "Inténtalo nuevamente."
        )


# ==================================================
# ENVIAR RESPUESTAS LARGAS
# ==================================================

async def enviar_texto_largo(mensaje, texto):

    limite = 3900

    if not texto:

        texto = "No hay información disponible."

    for inicio_texto in range(
        0,
        len(texto),
        limite
    ):

        parte = texto[
            inicio_texto:inicio_texto + limite
        ]

        await mensaje.reply_text(parte)


# ==================================================
# COMANDO START
# ==================================================

async def inicio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        """
🌎 ¡Hola! Soy TourBot Colombia.

✈️ ¡Tu compañero para descubrir Colombia!

Puedo ayudarte a conocer destinos increíbles,
su historia, gastronomía, actividades y mucho más.

📸 También puedes enviarme una fotografía
para intentar identificar el lugar.

🏖️ Playas
🏔️ Montañas
🌳 Naturaleza
🏙️ Ciudades

¿A dónde viajamos hoy?
""",

        reply_markup=teclado_principal()

    )


# ==================================================
# COMANDO DESTINOS
# ==================================================

async def destinos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        """
🌎 ¡Vamos a explorar Colombia!

Selecciona el tipo de destino que te gustaría conocer.

📸 También puedes enviarme una fotografía.
""",

        reply_markup=teclado_principal()

    )


# ==================================================
# RECIBIR FOTOGRAFÍAS
# ==================================================

async def responder_fotografia(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not cliente_gemini:

        await update.message.reply_text(
            "⚠️ No está configurada GEMINI_API_KEY."
        )

        return

    mensaje = update.message

    await mensaje.reply_text(
        "📸 ¡Qué buena foto!\n\n"
        "Estoy intentando identificar el lugar. 🔎"
    )

    try:

        # FOTOGRAFÍA NORMAL

        if mensaje.photo:

            archivo = await mensaje.photo[-1].get_file()

            imagen = await archivo.download_as_bytearray()

            mime_type = "image/jpeg"

        # IMAGEN ENVIADA COMO DOCUMENTO

        elif mensaje.document:

            documento = mensaje.document

            if (
                documento.file_size
                and documento.file_size > 20 * 1024 * 1024
            ):

                await mensaje.reply_text(
                    "⚠️ La imagen es demasiado grande.\n"
                    "Envía una imagen de menos de 20 MB."
                )

                return

            mime_type = documento.mime_type or "image/jpeg"

            if not mime_type.startswith("image/"):

                await mensaje.reply_text(
                    "El archivo enviado no parece ser una imagen."
                )

                return

            archivo_telegram = await documento.get_file()

            imagen = await archivo_telegram.download_as_bytearray()

        else:

            await mensaje.reply_text(
                "Por favor, envíame una fotografía."
            )

            return

        # IDENTIFICAR LUGAR

        identificacion, error = await identificar_fotografia(
            bytes(imagen),
            mime_type
        )

        if error:

            await mensaje.reply_text(error)

            return

        # GUARDAR LUGAR IDENTIFICADO

        context.user_data["lugar_fotografia"] = identificacion

        # MOSTRAR RESULTADO

        await mensaje.reply_text(

            f"""
🌎 ¡Mira lo que encontré!

{identificacion}

✨ ¿Qué te gustaría descubrir de este lugar?
""",

            reply_markup=teclado_fotografia()

        )

    except Exception as error:

        print(
            "Error procesando fotografía:",
            error
        )

        await mensaje.reply_text(
            "❌ Ocurrió un error al procesar tu fotografía.\n\n"
            "Intenta enviarla nuevamente."
        )


# ==================================================
# PROCESAR BOTONES
# ==================================================

async def procesar_boton(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    datos = query.data.split("|")

    accion = datos[0]

    # VOLVER AL MENÚ PRINCIPAL

    if accion == "inicio":

        context.user_data.clear()

        await query.edit_message_text(

            """
🌎 ¡Bienvenido nuevamente a TourBot Colombia!

¿Listo para descubrir otro destino?

Selecciona una categoría o envíame una fotografía.
""",

            reply_markup=teclado_principal()

        )

        return

    # OTRA FOTOGRAFÍA

    if accion == "otra_foto":

        context.user_data.pop(
            "lugar_fotografia",
            None
        )

        await query.edit_message_text(

            """
📸 ¡Vamos por otro destino!

Envíame una nueva fotografía
y trataré de identificar el lugar.
"""

        )

        return

    # CONSULTAR INFORMACIÓN

    if accion == "foto":

        tema = datos[1]

        lugar = context.user_data.get(
            "lugar_fotografia"
        )

        if not lugar:

            await query.edit_message_text(
                "No tengo un lugar identificado. "
                "Envíame nuevamente una fotografía."
            )

            return

        nombre_tema = TEMAS.get(tema)

        if not nombre_tema:

            await query.edit_message_text(
                "No encontré esa opción."
            )

            return

        await query.edit_message_text(

            f"""
🔎 ¡Vamos a descubrir más!

📍 Tema: {nombre_tema}

Un momento, estoy preparando la información...
"""

        )

        respuesta = await consultar_tema(
            lugar,
            tema
        )

        await enviar_texto_largo(
            query.message,
            respuesta
        )

        await query.message.reply_text(

            "✨ ¿Qué más quieres conocer de este lugar?",

            reply_markup=teclado_fotografia()

        )

        return

    # SELECCIONAR CATEGORÍA

    if accion == "cat":

        categoria = datos[1]

        if categoria not in DATOS:

            await query.edit_message_text(
                "Categoría no encontrada."
            )

            return

        context.user_data["categoria"] = categoria

        context.user_data.pop(
            "destino",
            None
        )

        context.user_data.pop(
            "lugar_fotografia",
            None
        )

        await query.edit_message_text(

            DATOS[categoria]["nombre"]
            + "\n\nSelecciona el destino que deseas explorar:",

            reply_markup=teclado_destinos(categoria)

        )

        return

    # SELECCIONAR DESTINO

    if accion == "dest":

        categoria = datos[1]

        destino = datos[2]

        if categoria not in DATOS:

            await query.edit_message_text(
                "Categoría no encontrada."
            )

            return

        destinos_categoria = DATOS[categoria]["destinos"]

        if destino not in destinos_categoria:

            await query.edit_message_text(
                "Destino no encontrado."
            )

            return

        nombre = destinos_categoria[destino]

        context.user_data["categoria"] = categoria

        context.user_data["destino"] = nombre

        context.user_data["lugar_fotografia"] = (
            f"{nombre}, Colombia"
        )

        await query.edit_message_text(

            f"""
📍 ¡Excelente elección!

Has seleccionado: {nombre} 🇨🇴

¿Qué quieres descubrir de este destino?
""",

            reply_markup=teclado_fotografia()

        )

        return


# ==================================================
# RESPONDER MENSAJES DE TEXTO
# ==================================================

async def responder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    texto_original = update.message.text

    texto = normalizar_texto(texto_original)

    categoria, confianza = analizar_texto(texto)

    print(
        "Mensaje recibido:",
        texto_original
    )

    print(
        "Categoría:",
        categoria
    )

    print(
        "Confianza:",
        round(confianza * 100, 2),
        "%"
    )

    # SI YA HAY UN DESTINO SELECCIONADO

    lugar = context.user_data.get(
        "lugar_fotografia"
    )

    if lugar:

        if confianza >= 0.20:

            equivalencias = {

                "gastronomia": "gastronomia",
                "hospedaje": "hospedaje",
                "transporte": "transporte"

            }

            tema = equivalencias.get(categoria)

            if tema:

                await update.message.reply_text(
                    "🔎 ¡Estoy preparando tu respuesta!"
                )

                respuesta = await consultar_tema(
                    lugar,
                    tema
                )

                await enviar_texto_largo(
                    update.message,
                    respuesta
                )

                await update.message.reply_text(

                    "✨ ¿Qué más quieres conocer?",

                    reply_markup=teclado_fotografia()

                )

                return

        await update.message.reply_text(

            "😊 Puedes seleccionar un tema del menú "
            "para seguir descubriendo este destino.",

            reply_markup=teclado_fotografia()

        )

        return

    # VALIDAR CATEGORÍA

    if confianza < 0.20 or categoria not in DATOS:

        await update.message.reply_text(

            """
🤔 No logré identificar qué tipo de destino buscas.

Puedes elegir entre:

🏖️ Playas
🏔️ Montañas
🌳 Naturaleza
🏙️ Ciudades

📸 También puedes enviarme una fotografía.

¡Vamos a descubrir Colombia! 🇨🇴
""",

            reply_markup=teclado_principal()

        )

        return

    # MOSTRAR DESTINOS

    await update.message.reply_text(

        f"""
¡Excelente elección! 😊

{DATOS[categoria]['nombre']}

Selecciona el destino que te gustaría explorar.
""",

        reply_markup=teclado_destinos(categoria)

    )


# ==================================================
# MANEJAR ERRORES DEL BOT
# ==================================================

async def manejar_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "Error del bot:",
        context.error
    )


# ==================================================
# EJECUTAR BOT
# ==================================================

def main():

    if not TOKEN:

        print(
            "ERROR: No se encontró el token de Telegram."
        )

        print(
            '$env:TELEGRAM_TOKEN="TU_TOKEN"'
        )

        return

    if not GEMINI_API_KEY:

        print(
            "ADVERTENCIA: No se encontró GEMINI_API_KEY. "
            "El bot funcionará sin reconocimiento de fotografías."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    # COMANDOS

    app.add_handler(
        CommandHandler(
            "start",
            inicio
        )
    )

    app.add_handler(
        CommandHandler(
            "destinos",
            destinos
        )
    )

    # BOTONES

    app.add_handler(
        CallbackQueryHandler(
            procesar_boton
        )
    )

    # RECIBIR FOTOGRAFÍAS

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            responder_fotografia
        )
    )

    # RECIBIR MENSAJES DE TEXTO

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            responder
        )
    )

    # ERRORES

    app.add_error_handler(
        manejar_error
    )

    print(
        "TourBot Colombia está funcionando..."
    )

    app.run_polling()


# ==================================================
# INICIAR PROGRAMA
# ==================================================

if __name__ == "__main__":

    main()
