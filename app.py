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
                    messenger.send_template("eventbot_presentation", mobile, components=[], lang="es_ES")
                    button={
                            "header": "Menú principal",
                            "body": "Elige una de las siguientes opciones",
                            "footer": "EventBot - WakeUp & Dream - Ménú Principal",
                            "action": {
                                "button": "OPCIONES",
                                "sections": [
                                    {
                                        "title": "Información general",
                                        "rows": [
                                            {"id": "row 1", "title": "Info general entradas", "description": "Información general sobre las entradas, página de venta y precios."},
                                            {
                                                "id": "row 2",
                                                "title": "Ayuda proceso de compra",
                                                "description": "Errores durante la compra, la entrada no te ha llegado, no sabes como descargarla, tienes un cargo duplicado en tu cuenta, etc ...",
                                            },
                                            {
                                                "id": "row 3",
                                                "title": "LINE UP",
                                                "description": "LINE UP con todos los artistas.",
                                            },
                                            {
                                                "id": "row 4",
                                                "title": "Localización y zonas de aparcamiento",
                                                "description": "Te enviamos el mapa de las zonas para estacionar vehículos.",
                                            },
                                            {
                                                "id": "row 5",
                                                "title": "Mapa del Festival",
                                                "description": "Te enviamos un mapa completo del festival para que lo tengas en tu teléfono.",
                                            }
                                        ]
                                    },
                                    {
                                        "title": "Transporte",
                                        "rows": [
                                            {"id": "row 7", "title": "Taxis", "description": "Información sobre taxis y otros servicios similares"},
                                            {
                                                "id": "row 8",
                                                "title": "Buses",
                                                "description": "Información sobre las líneas de autobús.",
                                            },
                                           
                                        ]
                                    },
                                    {
                                        "title": "Otras preguntas frecuentes",
                                        "rows": [
                                            {"id": "row 7", "title": "Normas de acceso", "description": "¿Puedo acceder con bebida o comida al recinto?, ¿Tengo que ser mayor de 18 años?, ¿Qué pasa si pierdo mi entrada durante el festival?, etc ..."},
                                            {
                                                "id": "row 8",
                                                "title": "Alojamiento",
                                                "description": "¿Contáis con camping o glamping?, ¿Qué sitios son buenos para alojarse cerca del evento?, etc ...",
                                            },
                                           
                                        ]
                                    }
                                ]
                            }
                        }
                
                        messenger.send_button(button,mobile)

                elif message_type == "interactive":
                    message_response = messenger.get_interactive_response(data)
                    intractive_type = message_response.get("type")
                    message_id = message_response[intractive_type]["id"]
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


if __name__ == '__main__': 
    app.run(debug=True)
