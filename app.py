import os
import logging
import json
import mysql.connector
import datetime
import random
from heyoo import WhatsApp
from os import environ
from flask import Flask, request, make_response
import pickle
import numpy as np
from llama_index import LLMPredictor, GPTVectorStoreIndex, SimpleDirectoryReader,PromptHelper, ServiceContext, StorageContext, GPTVectorStoreIndex,load_index_from_storage, QuestionAnswerPrompt
from langchain.chat_models import ChatOpenAI
import os
import config


messenger = WhatsApp(environ.get("TOKEN"), phone_number_id=environ.get("PHONE_NUMBER_ID")) #this should be writen as 
#WhatsApp(token = "inpust accesstoken", phone_number_id="input phone number id") #messages are not recieved without this pattern

os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY

# Here's an article on how to get the application secret from Facebook developers portal.
# https://support.appmachine.com/support/solutions/articles/80000978442
VERIFY_TOKEN = environ.get("APP_SECRET") #application secret here

#to be tested in prod environment
# messenger = WhatsApp(os.getenv("heroku whatsapp token"),phone_number_id='105582068896304')
# VERIFY_TOKEN = "heroku whatsapp token"


# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = Flask(__name__)



@app.route('/')
def index():
    return "Hello, It Works"



@app.route("/whatsapi", methods=["GET", "POST"])
def hook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            logging.info("Verified webhook")
            response = make_response(request.args.get("hub.challenge"), 200)
            response.mimetype = "text/plain"
            return response
        logging.error("Webhook Verification failed")
        return "Invalid verification token"

    # Handle Webhook Subscriptions
    data = request.get_json()
    logging.info("Received webhook data: %s", data)
    changed_field = messenger.changed_field(data)
    changes = data['entry'][0]['changes'][0]['value']
    
    
    if (data['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']) == environ.get("PHONE_NUMBER_ID"):
        
        if changed_field == "messages":
            new_message = messenger.get_mobile(data)
            if new_message:
                mobile = messenger.get_mobile(data)
                name = messenger.get_name(data)
                message_type = messenger.get_message_type(data)
                logging.info(
                    f"New Message; sender:{mobile} name:{name} type:{message_type}"
                )
                if message_type == "text":

                    message = messenger.get_message(data)
                    name = messenger.get_name(data)
                    logging.info("Message: %s", message)
                    #Imprimir menú principal y mensaje de bienvenida
                    

                    #MENSAJE ENVIADO POR LA EMPRESA
                    
                    
                    #no trae campo CONVERSATION - MENSAJE ENVIADO POR EL USUARIO
                    

                    phone_tup = (mobile,)
                    try:
                        connection = mysql.connector.connect(host='cerobyte.com',
                                                 database='wakeup_and_dream_bot',
                                                 user='wakeup_and_dream_bot',
                                                 password='Sck85#97q')

                        query_user = "SELECT * from wakeup_bot where phone = %s"
                        cursor = connection.cursor()
                        consulta = cursor.execute(query_user, phone_tup)

                        # get all records
                        records = cursor.fetchall()
                       
                        if not len(records):
                                sql = "INSERT INTO wakeup_bot (phone) VALUES (%s)"
                                val = (mobile,)
                                cursor.execute(sql,val)
                                connection.commit()
                                messenger.send_message(f'''¡Hola, {name}!''',mobile)
                    except Exception as err:
                        messenger.send_message(str(err),mobile)
                    #############################################################
                    #COSAS ALEATORIAS PARA MANDAR SI YA ESTABLECIMOS CONVERSACIÓN#
                    #############################################################
                    
                    #messenger.send_message(f"Quedan {countdown.days} días",mobile)
                    if checkprimeravezen24(mobile) == True:
                        #https://gpt-index.readthedocs.io/en/latest/how_to/customization/custom_prompts.html

                        query_str = message
                        context_str = "Eres un asistente virtual destinado a ayudar a los clientes en un festival llevado a cabo en A Coruña el 14 y 15 de Julio de 2023"
                        QA_PROMPT_TMPL = (
                                "Proporcionamos información del contexto a continuación. \n"
                                "---------------------\n"
                                "{context_str}"
                                "\n---------------------\n"
                                "Dada esta información, por favor responde a la pregunta: {query_str}\n"
                        )
                        QA_PROMPT = QuestionAnswerPrompt(QA_PROMPT_TMPL)
                        llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="ada-v2"))
                        max_input_size = 4096
                        num_output = 256
                        max_chunk_overlap = 20
                        prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
        
                        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
                        storage_context = StorageContext.from_defaults(persist_dir="storage") 
                        index = load_index_from_storage(storage_context)
                        query_engine = index.as_query_engine(text_qa_template=QA_PROMPT) 
                        response = query_engine.query(message)
                        messenger.send_message(str(response),mobile)
                        menuprincipal(mobile)
                        


                elif message_type == "interactive":
                    message_response = messenger.get_interactive_response(data)
                    intractive_type = message_response.get("type")
                    message_id = message_response[intractive_type]["id"]

                    #volver al menú principal
                    if message_id == "menu_si":
                        menuprincipal(mobile)

                    ####################################################### AYUDA COMPRA ######################################################################
                    elif message_id == "ayudacompra":
                       
                        #Enviar mensaje template ayuda compra.
                        messenger.send_template("eventbot_ayudacompra", mobile, components=[], lang="es_ES")
                        boton_ayuda_compra(mobile)

                    elif message_id == "infogeneral_nollegaentrada":
                        messenger.send_template("eventbot_nollegaentrada", mobile, components=[], lang="es_ES")
                        #messenger.send_message(f"Los *tickets* son gestionados directamente por la *plataforma online de venta* 🎟. Te enviamos un email y un número de teléfono para que te puedas poner en contacto con ellos y recuperar los tuyos 😊", mobile)
                        messenger.send_message(f"info@ayudaeventos.com",mobile)
                        enviarcontacto_eata(mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "infogeneral_cargoduplicado":
                        messenger.send_template("eventbot_cargoduplicado", mobile, components=[], lang="es_ES")
                        #messenger.send_message(f"*¡No te preocupes!* 👽 Esto es algo habitual en las pasarelas de pago online. Te enviamos un número de teléfono para que contactes con la plataforma de venta de tickets en horario laboral", mobile)
                        enviarcontacto_eata(mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "infogeneral_otros":
                        #messenger.send_template("eventbot_ayudaotros", mobile, components=[], lang="es_ES")
                        messenger.send_message('''*OTRAS DUDAS*
Si tu pregunta no está relacionada con aspectos técnicos en cuanto a la plataforma de venta de tickets 🎟, puedes enviarnos un MD por *Instagram* e intentaremos contestarte lo antes posible
https://instagram.com/wakeupand_dreamfestival
                            ''',mobile)
                        fecha_festival = '2023/07/14'
                        fecha_festival_d1 = datetime.datetime.strptime(fecha_festival, "%Y/%m/%d")
                        present = datetime.datetime.now()
                        countdown = fecha_festival_d1 - present
                        frases_aleatorias = ['''*¡Ya queda menos!*⌚
Échale un vistazo a nuestra web si todavía no la has visitado 😃 https://wakeupanddreamfestival.com
Si *tienes dudas* puedes seleccionar una opción del menú''',
'''*Muy pronto* habilitaremos las *ZONAS VIP* 🍾
Podrás hacerte con un espacio único para disfrutar del festival con mayor comodidad
Si *tienes dudas* puedes seleccionar una opción del menú''',
'''No te olvides de seguirnos en *Instagram* 😉
https://instagram.com/wakeupand_dreamfestival
Si *tienes dudas* puedes seleccionar una opciión del menú''',
"¡{name}!, Quedan menos de *{countdown} días* 🕒 para el festi del verano.Si *tienes dudas* puedes seleccionar una opción del menú"]
                        messenger.send_message(f"{random.choice(frases_aleatorias)}",mobile)
                        messenger.send_message(f"Elige una de las opciones del menú",mobile)
                        menuprincipal(mobile)

                    elif message_id == "geoyparking":
                        messenger.send_message('''Disponemos de una *ZONA DE APARCAMIENTO* en el recinto 🚗.
A pesar de ello, *RECOMENDAMOS* asistir al festival en *TRANSPORTE PÚBLICO* 🚌
Si seleccionas esta opción más adelante, te enviaré al instante la ubicación exacta de la zona.''', mobile)
                        volveralmenuprincipal(mobile)

                        ############################################################ MAPA FESTI ####################################################################

                    elif message_id == "mapafesti":
                        messenger.send_message('''MAPA DEL FESTIVAL
Más adelante subiremos aquí el *mapa completo del festival*''', mobile)
                        volveralmenuprincipal(mobile)

                        ###########################################################################################################################################

                    elif message_id == "infogeneral":
                        messenger.send_message('''*VENTA DE TICKETS* 🎟️

En nuestra página web tienes la información relevante acerca del festival 🎡 https://wakeupanddreamfestival.com

Puedes adquirir tus *tickets* 🎟️ aquí https://wakeupanddreamfestival.com/tickets/

*TIRADAS*

- *ABONO GENERAL (39€ + G.D)* - *AGOTADO*
- *ABONO GENERAL (45€ + G.D)* - *AGOTADO*
- *ABONO GENERAL (50€ + G.D)* - *AGOTADO*
- *ABONO GENERAL (55€ + G.D)* - *DISPONIBLES*
    ''', mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "taxis":
                        messenger.send_message(f'''TAXI 🚕

- *Servicio de Taxis RadioTaxi - A Coruña*: +34  981 24 33 33
- *Servicio de Taxis Teletaxi - A Coruña* : +34 981 28 77 77''', mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "autobus":
                        messenger.send_message(f'''LÍNEAS DE AUTOBÚS 🚌

Más adeante subiremos aquí las líneas de autobús urbano para llegar al recinto''', mobile)
                        volveralmenuprincipal(mobile)
                    
                    elif message_id == "masopciones":
                        messenger.send_message(f'''OPCIONES EXTRA 🚌

Durante el Festival se habilitarán las siguientes funcionalidades:
- *Localización de barras, puntos de venta, zonas vip, servicios, etc ... en tiempo real*

- *Solicitud de ayuda en tiempo real con envío de geolocalización y aviso a servicios de emergencia locales*

- *Itinerario de actividades para realizar en la ciudad*

- *Recomendación de actividades, sitios de ocio y restauración*

- *Listado de precios en tiempo real*

- *Sección de noticias actualizada para ver todas las novedades durante el evento*

- *Sorteos automatizados*

- *Por solo 1€ al día (durante la duración del festival) te informaremos constantemente sobre cambios, noticias, aviso de comienzo de actuaciones, situación en tiempo real de aforo, fotografías, etc ...*''', mobile)
                        volveralmenuprincipal(mobile)

                        
                        ############################################################ LINEUP #####################################################################
                    elif message_id == "lineup":
                        messenger.send_image('https://i.ibb.co/58X961H/wakeupfest.jpg',mobile)
                        button_reply={
                "type": "button",
                "body": {
                    "text": "¿Quieres que te envíe los perfiles de Instagram de lxs artistas?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "b1",
                                "title": "SÍ"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "b2",
                                "title": "NO"
                            }
                        }
                    ]
                }
        }
                        messenger.send_reply_button(button_reply,mobile)
                    elif message_id == "b1":
                        messenger.send_message('''🔥*LINE UP* 🔥''',mobile)
                        messenger.send_message(''' *14 DE JULIO* ''',mobile)
                        messenger.send_message('''*CARL COX INVITES*
    https://instagram.com/carlcoxofficial''',mobile)
                        messenger.send_message('''*ANDREA OLIVA*
    https://instagram.com/andreaoliva1''',mobile)
                        messenger.send_message('''*CHELINA MANUHUTU*
    https://instagram.com/chelinamanuhutu''',mobile)
                        messenger.send_message('''*FATIMA HAJJI*
    https://instagram.com/fatimahajji''',mobile)
                        messenger.send_message('''*SQUIRE*
    https://instagram.com/squire.music''',mobile)
                        messenger.send_message('''*SELLES*
    https://instagram.com/selles.dj''',mobile)
                        messenger.send_message('''*ANDRE V*''',mobile)
                        messenger.send_message(''' *15 DE JULIO* ''',mobile)
                        messenger.send_message('''*AMELIE LENS*
    https://instagram.com/amelie_lens''',mobile)
                        messenger.send_message('''*KLANGKUENSTLER*
    https://instagram.com/klangkuenstler''',mobile)
                        messenger.send_message('''*BEN SIMS*
    https://instagram.com/bensimsofficial''',mobile)
                        messenger.send_message('''*ANDRES CAMPO*
    https://instagram.com/andrescampo''',mobile)
                        messenger.send_message('''*GONÇALO B2B RAUL PACHECO*
    https://instagram.com/goncalomusic
    https://instagramc.com/raulpacheco_''',mobile)
                        messenger.send_message('''*JOYHAUSER*
    https://instagram.com/joyhauser_ ''',mobile)
                        messenger.send_message('''*MANU SANCHEZ*
    https://instagram.com/manusanchez__''',mobile)
                        volveralmenuprincipal(mobile)
                    elif message_id == "b2":
                        volveralmenuprincipal(mobile)



                    ###########################################################################################################################################


                    message_text = message_response[intractive_type]["title"]
                    logging.info(f"Interactive Message; {message_id}: {message_text}")

                    #########################################################GEO Y PARKING#####################################################################

                    ############################################################ MAPA FESTI ####################################################################

                elif message_type == "location":
                    message_location = messenger.get_location(data)
                    message_latitude = message_location["latitude"]
                    message_longitude = message_location["longitude"]
                    logging.info("Location: %s, %s", message_latitude, message_longitude)

                elif message_type == "image":
                    image = messenger.get_image(data)
                    image_id, mime_type = image["id"], image["mime_type"]
                    image_url = messenger.query_media_url(image_id)
                    image_filename = messenger.download_media(image_url, mime_type)
                    print(f"{mobile} sent image {image_filename}")
                    logging.info(f"{mobile} sent image {image_filename}")

                elif message_type == "video":
                    video = messenger.get_video(data)
                    video_id, mime_type = video["id"], video["mime_type"]
                    video_url = messenger.query_media_url(video_id)
                    video_filename = messenger.download_media(video_url, mime_type)
                    print(f"{mobile} sent video {video_filename}")
                    logging.info(f"{mobile} sent video {video_filename}")

                elif message_type == "audio":
                    audio = messenger.get_audio(data)
                    audio_id, mime_type = audio["id"], audio["mime_type"]
                    audio_url = messenger.query_media_url(audio_id)
                    audio_filename = messenger.download_media(audio_url, mime_type)
                    print(f"{mobile} sent audio {audio_filename}")
                    logging.info(f"{mobile} sent audio {audio_filename}")

                elif message_type == "document":
                    file = messenger.get_document(data)
                    file_id, mime_type = file["id"], file["mime_type"]
                    file_url = messenger.query_media_url(file_id)
                    file_filename = messenger.download_media(file_url, mime_type)
                    print(f"{mobile} sent file {file_filename}")
                    logging.info(f"{mobile} sent file {file_filename}")
                else:
                    print(f"{mobile} sent {message_type} ")
                    print(data)
            else:
                delivery = messenger.get_delivery(data)
                if delivery:
                    print(f"Message : {delivery}")
                else:
                    print("No new message")
        if 'errors' in changes:
            return "ok"
        if 'statuses' in changes:
            mobile = changes['statuses'][0]['recipient_id']
        
            #print(f"STAUTES: {statuses}")
            print({mobile})
            if mobile != None:
                #smobile = messenger.get_mobile(data)
            
                
            
                phone_tup = (str(mobile),)
              
                try:
                        connection = mysql.connector.connect(host='cerobyte.com',
                                                        database='wakeup_and_dream_bot',
                                                        user='wakeup_and_dream_bot',
                                                        password='Sck85#97q')

                        query_user = "SELECT count(*) from wakeup_bot where phone = %s"
                        cursor = connection.cursor()
                        consulta = cursor.execute(query_user, phone_tup)

                            # get all records
                        records = cursor.fetchall()
                        
                        
                        delivery = messenger.get_delivery(data)
                        if delivery == "sent":
                            conversation_id = changes['statuses'][0]['conversation']['id']
                            timestamp_caduca24h = changes['statuses'][0]['conversation']['expiration_timestamp']
                            if checkprimeravezen24(mobile) == False:
                                #Si no hay registros, añadimos el número de teléfono y el id de la conversación
                                #ESTO CREO QUE ES SI LA EMPIEZA LA EMPRESA
                                #Primera vez que entra DESDE SIEMPRE
                                if not len(records):
                                    #insertar y enviar mensaje nuevo
                                    
                                    sql = "INSERT INTO wakeup_bot (phone, last_conver, check24h) VALUES (%s,%s,%s)"
                                    val = (mobile, conversation_id,1)
                                    cursor.execute(sql,val)
                                    connection.commit()
                                    #messenger.send_message(f"Soy EventBot 🤖, tu asistente personal durante todo el *Wake Up & Dream*. Soy un poco torpe y a las 24h me reinicio para descansar y olvido toda nuestra conversación 😇. Toda la información que necesitas está disponible a través del *MENÚ PRINICPAL* que aparece a continuación.",mobile)
                                        #menuprincipal(mobile)
                                elif records[0][0] != conversation_id:
                                    #Ya ha entrado pero la conversación no es la misma
                                    tup = (conversation_id,mobile,timestamp_caduca24h)
                                    mobile_tup = (mobile,)
                                    #update y enviar mensaje nuevo
                                    messenger.send_message(f"Soy EventBot 🤖, tu asistente personal durante todo el *Wake Up & Dream*. Soy un poco torpe y a las 24h me reinicio para descansar y olvido toda nuestra conversación 😇. Toda la información que necesitas está disponible a través del *MENÚ PRINICPAL* que aparece a continuación. También puedes escribirme directamente y te daré distinta información sobre el festival.",mobile)
                                    cursor = connection.cursor()
                                    cursor.execute('''UPDATE wakeup_bot SET last_conver = %s WHERE phone = %s''',tup)
                                    cursor.execute('''UPDATE wakeup_bot SET check24h = 1 WHERE phone = %s''',mobile_tup)
                                    connection.commit()
                                    menuprincipal(mobile)
                                

                            
                                    #frases aleatorias
                                elif records[0][0] == conversation_id:
                                    return "ok"

                except Exception as err:
                    print(err)
                                    
                            
            
            
    return "ok"

def volveralmenuprincipal(mobile):
    button={
                            "type": "button",
                            "body": {
                                "text": "¿Quieres volver al menú principal?"
                            },
                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "menu_si",
                                            "title": "Sí"
                                        }
                                    }                        
                                ]
                            }
                        }
    messenger.send_reply_button(button,mobile)

def menuprincipal(mobile):
    button={
                            "header": "Menú principal",
                            "body": "Elige una de las siguientes opciones",
                            "footer": "WakeUp & Dream - EventBot",
                            "action": {
                                "button": "Lista de Opciones",
                                "sections": [
                                    {
                                        "title": "Información general",
                                        "rows": [
                                            {"id": "infogeneral", "title": "Info general de tickets", "description": "Información general sobre la venta de tickets."},
                                            {
                                                "id": "ayudacompra",
                                                "title": "Ayuda proceso de compra",
                                                "description": "Tickets no recibidos, cargos duplicados, etc ...",
                                            },
                                            {
                                                "id": "lineup",
                                                "title": "Line Up",
                                                "description": "Line Up actualizado con todos los artistas.",
                                            },
                                            {
                                                "id": "geoyparking",
                                                "title": "Localización y parking",
                                                "description": "Localización del festival y aparcamientos.",
                                            },
                                            {
                                                "id": "mapafesti",
                                                "title": "Mapa del festival",
                                                "description": "Mapa completo por zonas del festival.",
                                            }
                                        
                                        ]
                                    },
                                    {
                                        "title": "Llegar al festival",
                                        "rows": [
                                            {"id": "taxis", "title": "Taxi", "description": "Información sobre taxis y transporte similar"},
                                            {
                                                "id": "autobus",
                                                "title": "Autobús",
                                                "description": "Lista y mapa con las líneas de transporte público de la ciudad.",
                                            },
                                            {
                                                "id": "masopciones",
                                                "title": "Más Opciones",
                                                "description": "Opciones extra",
                                            }

                                                 
                                        ]
                                    }
                                ]
                            }
                        }
    messenger.send_button(button,mobile)
def checkprimeravezen24(mobile):
    val_mobile = (str(mobile),)
    try:
        connection = mysql.connector.connect(host='cerobyte.com',
                                                     database='wakeup_and_dream_bot',
                                                     user='wakeup_and_dream_bot',
                                                     password='Sck85#97q')

        query_user = "SELECT check24h from wakeup_bot where phone = %s"
        cursor = connection.cursor()
        consulta = cursor.execute(query_user, val_mobile)

        # get all records
        records = cursor.fetchall()
        if not len(records):
            return False
        if records[0][0] == 1:
            return True
        else:
            return False

    except Exception as err:
        print(err)

def boton_ayuda_compra(mobile):
    try:
        button_ayudacompra={
                                "header": "Ayuda proceso de compra",
                                "body": "Elige una de las siguientes opciones",
                                "footer": "WakeUp & Dream - EventBot",
                                "action": {
                                    "button": "Lista de Opciones",
                                    "sections": [
                                        {
                                            "title": "Problemas entradas",
                                            "rows": [
                                                {"id": "infogeneral_nollegaentrada", "title": "Ticket(s) no recibido(s)", "description": ""},
                                                {
                                                    "id": "infogeneral_cargoduplicado",
                                                    "title": "Cargo duplicado",
                                                    "description": "",
                                                },
                                                {
                                                    "id": "infogeneral_otros",
                                                    "title": "Otros problemas",
                                                    "description": "",
                                                }
                                            
                                            ]
                                        }
                                    ]
                                }
                        }
        messenger.send_button(button_ayudacompra,mobile)
    except Exception as err:
        messenger.send_message('No puedo procesar esta petición ahora.',mobile)
def enviarcontacto_eata(mobile):
    try:
        contacts = [{
      "name": {
        "formatted_name": "Entradasatualcance",
        "first_name": "Entradasatualcance"
      },
      "emails": [{
          "email": "info@ayudaeventos.com",
          "type": "WORK"
        }
        ],
      "org": {
        "company": "ENTRADAS A TU ALCANCE",
        "department": "VENTA DE TICKETS"
      },
      "phones": [{
          "phone": "+34910053595",
          "type": "WORK"
        }
        ],
    }]
        messenger.send_contacts(contacts, mobile)

    except Exception as err:
        messenger.send_message("No puedo procesar esta petición ahora",mobile)

def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.80
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    if not ints:
        tag = "noanswer"
    else:
        tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result

def chatbot_response(msg):
    respuesta = dict();
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    respuesta['res'] = res
    if ints:
        respuesta['ints'] = ints[0]['intent']

    return respuesta




if __name__ == '__main__': 
    app.run(debug=True)
