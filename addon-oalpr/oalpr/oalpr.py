import logging
import signal
import sys
from base64 import b64decode

from flask import Flask, request, jsonify
from openalpr import Alpr

LOG_FILE = '/config/oalpr/log/oalpr.log'
IMAGE_FILE = '/config/oalpr/data/plate.jpg'

logging.basicConfig(filename=LOG_FILE, filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
lpr = Alpr("eu", "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")
#lpr.set_default_region("eu")
if not lpr.is_loaded():
    logging.error("Error loading OpenALPR")
    sys.exit(1)


@app.route('/recognize', methods=['POST'])
def recognize():
    logging.info("Starting recognition")
    image_bytes = request.form.get("image_bytes")    
    image = b64decode(image_bytes)    
    with open("/config/oalpr/data/uploaded.jpg","wb") as f :
        f.write(image)
    lpr_results = lpr.recognize_array(image)
    logging.info(f"Starting recognition {lpr_results}")   
    
    recognized_plates = ""
    for result in lpr_results["results"]:
        recognized_plates = result["plate"]

    if recognized_plates == "":
        text = "No plates recognized"
    else:
        text = "Recognized plates {}".format(recognized_plates)

    logging.info(text)

    return jsonify({'plate' : lpr_results})

def signal_handler(sig, frame):
    logging.info('Received SIGINT. Unloading ALPR')
    lpr.unload()
    sys.exit(0)


try:
    signal.signal(signal.SIGINT, signal_handler)
    logging.info('ALPR loaded. Ready to recognize')
    app.run(host='0.0.0.0',port=5001)
except Exception as e:
    logging.error("Exception occurred", exc_info=True)
