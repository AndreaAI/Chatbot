"""
Description:    Flask application that handles post requests to and hands the off to the appropriate functions.
Author:     Andrea Aguilar Ibáñez
"""

import logging
import os
from datetime import datetime
import pusher
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from chatbot_searchClass import searchClass

REVIEW_FOLDER = os.path.join('static', 'hotel_reviews')  # pointer to reviews
app = Flask(__name__)
dotenvpath = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenvpath)

socketId = 0
app.config['UPLOAD_FOLDER'] = REVIEW_FOLDER
# initialize Pusher
pusher_client = pusher.Pusher(
    app_id=os.getenv('PUSHER_APP_ID'),
    key=os.getenv('PUSHER_KEY'),
    secret=os.getenv('PUSHER_SECRET'),
    cluster=os.getenv('PUSHER_CLUSTER'),
    ssl=True)
instanceDict = {}  # global store to keep track of various instances going on


# above is imports and global initialisations
def pause():
    programPause = input("pause \n")


@app.route('/')  # homepage response
def index():
    return render_template('index.html')


@app.route('/closefile', methods=['POST'])
def close_file():
    socketId = request.form['socketId']
    if socketId in instanceDict:
        print('closing object')
        del instanceDict[socketId]
    return 'bye!'


@app.route('/send_message', methods=['POST'])  # send message post request
def send_message():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)  # sets up the logger
    logging.basicConfig(filename='ChatbotLog.log', level=logging.INFO)  # declares level of # logging
    logging.info('---------------------------------')
    logging.info('i started this process at {}'.format(datetime.now()))
    socketId = request.form['socketId']  # find users socketid
    logging.info("main socketId: {}".format(socketId))
    if socketId not in instanceDict:
        instanceDict.update({socketId: searchClass(socketId)})
    # create fresh instance if socketID hasnt been seen before
    message = request.form['message']
    logging.info("MESSAGE: {}".format(message))  # output users message to server
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    fulfillment_text = instanceDict[socketId].detect_intent_texts(project_id, socketId, message, 'en')
    # figure our what was said
    logging.info("fulfillment_text: {}".format(fulfillment_text))  # convert response into string just in case
    response_text = {"message": fulfillment_text, "location": instanceDict[socketId].location}  # put it into a dict

    return jsonify(response_text)  # jsonify and give response back to html side


# To connect with the Dialogflow 
@app.route('/get_hotel_detail', methods=['POST'])
def get_hotel_detail():
    data = request.get_json(silent=True)  # gets json that was created by Dialogflow for reading
    logging.info("DATA: {}".format(data))  # print on server screen
    for objectkey in instanceDict:  # check if user instance exists
        # users can only reach here if they're session has been noted, otherwise crash
        if objectkey in data['session']:
            socketId = objectkey  # change pointer to correct instance
            response = instanceDict[objectkey].handle_input(data)
            return response
    logging.info("ERROR COULDN'T FIND OBJECT")


# run Flask app
if __name__ == "__main__":
    app.run(debug=True, load_dotenv=True, use_debugger=False,
            use_reloader=False, passthrough_errors=True, host='localhost', port=5000)
