import os
import logging
import json
from heyoo import WhatsApp
from os import environ
from flask import Flask, request, make_response


messenger = WhatsApp(environ.get("TOKEN"), phone_number_id=environ.get("PHONE_NUMBER_ID")) #this should be writen as 
#WhatsApp(token = "inpust accesstoken", phone_number_id="input phone number id") #messages are not recieved without this pattern


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
                    #messenger.send_template("eventbot_presentation", mobile, components=[], lang="es_ES")
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
                        #messenger.send_template("eventbot_ayudacompra", mobile, components=[], lang="es_ES")
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

                    elif message_id == "infogeneral_nollegaentrada":
                        #messenger.send_template("eventbot_nollegaentrada", mobile, components=[], lang="es_ES")
                        messenger.send_message(f"Los *tickets* son gestionados directamente por la *plataforma online de venta* 🎟. Te enviamos un email y un número de teléfono para que te puedas poner en contacto con ellos y recuperar los tuyos 😊", mobile)
                        messenger.send_message(f"info@ayudaeventos.com",mobile)
                        enviarcontacto_eata(mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "infogeneral_cargoduplicado_otros":
                        #messenger.send_template("eventbot_cargoduplicado", mobile, components=[], lang="es_ES")
                        messenger.send_message(f"*¡No te preocupes!* 👽 Esto es algo habitual en las pasarelas de pago online. Te enviamos un número de teléfono para que contactes con la plataforma de venta de tickets en horario laboral",mobile)
                        volveralmenuprincipal(mobile)

                    elif message_id == "infogeneral_otros":
                        #messenger.send_template("eventbot_ayudaotros", mobile, components=[], lang="es_ES")
                        volveralmenuprincipal(mobile)

                    
                    ###########################################################################################################################################



                    message_text = message_response[intractive_type]["title"]
                    logging.info(f"Interactive Message; {message_id}: {message_text}")

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
                                            }
                                                 
                                        ]
                                    }
                                ]
                            }
                        }
    messenger.send_button(button,mobile)

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
        messenger.send_message(str(err),mobile)
            
if __name__ == '__main__': 
    app.run(debug=True)
