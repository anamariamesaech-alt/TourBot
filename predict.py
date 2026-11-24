
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


# ==========================================
# DATOS DE ENTRENAMIENTO
# ==========================================

mensajes = [

    # PLAYAS
    "Quiero conocer playas",
    "Recomiendame una playa",
    "Me gustan los destinos de mar",
    "Quiero ir a la costa",
    "Busco vacaciones en el caribe",
    "Quiero conocer islas y playas",
    "Donde puedo nadar en el mar",
    "Quiero viajar a Cartagena o Santa Marta",

    # MONTAÑAS
    "Me gustan las montañas",
    "Quiero hacer senderismo",
    "Busco destinos de montaña",
    "Quiero visitar lugares altos",
    "Quiero conocer el Valle del Cocora",
    "Busco paisajes de montañas",
    "Quiero caminar por senderos",
    "Me gustaría visitar Salento",

    # NATURALEZA
    "Quiero conocer la naturaleza",
    "Me gustan los paisajes naturales",
    "Quiero visitar parques naturales",
    "Busco lugares con mucha vegetacion",
    "Quiero conocer la selva",
    "Me interesa observar animales y aves",
    "Quiero visitar el Amazonas",
    "Busco turismo ecologico",

    # CIUDADES
    "Quiero conocer ciudades",
    "Recomiendame una ciudad",
    "Me gustan los lugares historicos",
    "Quiero visitar pueblos bonitos",
    "Quiero conocer museos y monumentos",
    "Busco planes culturales",
    "Quiero visitar Medellin o Bogota",
    "Me interesa conocer la cultura de Colombia",

    # GASTRONOMÍA
    "Donde puedo comer",
    "Quiero probar comida tipica",
    "Recomiendame restaurantes",
    "Que platos tipicos hay",
    "Cual es la gastronomia del destino",
    "Que comida tradicional puedo probar",
    "Quiero conocer los platos de la region",
    "Donde venden comida local",

    # HOSPEDAJE
    "Donde puedo hospedarme",
    "Busco un hotel",
    "Necesito alojamiento",
    "Recomiendame hospedajes",
    "Quiero encontrar un lugar para dormir",
    "Que hoteles hay en ese lugar",
    "Donde puedo reservar una habitacion",
    "Busco una posada o un hostal",

    # TRANSPORTE
    "Como puedo llegar",
    "Que transporte puedo utilizar",
    "Como llego a ese destino",
    "Necesito informacion de transporte",
    "Como me puedo movilizar",
    "Hay buses para llegar",
    "Donde tomo un taxi",
    "Como llego desde el aeropuerto"
]


# ==========================================
# CATEGORÍAS DE CADA MENSAJE
# ==========================================

categorias = [

    # PLAYAS
    "playa", "playa", "playa", "playa",
    "playa", "playa", "playa", "playa",

    # MONTAÑAS
    "montana", "montana", "montana", "montana",
    "montana", "montana", "montana", "montana",

    # NATURALEZA
    "naturaleza", "naturaleza", "naturaleza", "naturaleza",
    "naturaleza", "naturaleza", "naturaleza", "naturaleza",

    # CIUDADES
    "ciudad", "ciudad", "ciudad", "ciudad",
    "ciudad", "ciudad", "ciudad", "ciudad",

    # GASTRONOMÍA
    "gastronomia", "gastronomia", "gastronomia", "gastronomia",
    "gastronomia", "gastronomia", "gastronomia", "gastronomia",

    # HOSPEDAJE
    "hospedaje", "hospedaje", "hospedaje", "hospedaje",
    "hospedaje", "hospedaje", "hospedaje", "hospedaje",

    # TRANSPORTE
    "transporte", "transporte", "transporte", "transporte",
    "transporte", "transporte", "transporte", "transporte"
]


# ==========================================
# CREAR EL MODELO
# ==========================================

modelo = Pipeline([

    (
        "vectorizador",

        TfidfVectorizer(
            strip_accents="unicode",
            ngram_range=(1, 2)
        )
    ),

    (
        "clasificador",

        LogisticRegression(
            max_iter=1000
        )
    )

])


# ==========================================
# ENTRENAR EL MODELO
# ==========================================

modelo.fit(mensajes, categorias)


# ==========================================
# ANALIZAR MENSAJES
# ==========================================

def analizar_texto(texto):

    resultado = modelo.predict([texto])[0]

    confianza = modelo.predict_proba([texto]).max()

    return resultado, confianza


# ==========================================
# PROBAR EL MODELO
# ==========================================

if __name__ == "__main__":

    while True:

        texto = input(
            "\nEscribe una pregunta turística (o 'salir'): "
        )

        if texto.lower().strip() == "salir":

            print("Prueba finalizada.")
            break

        categoria, confianza = analizar_texto(texto)

        print(
            "Categoría identificada:",
            categoria
        )

        print(
            "Nivel de confianza:",
            round(confianza * 100, 2),
            "%"
        )
