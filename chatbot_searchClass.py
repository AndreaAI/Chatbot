"""
Description:    Class that is used to process users input and call alternate functions,
                class/object allows for users to have their own unique version, prevents bleed over if multiple users
Author:         Andrea Aguilar Ibáñez
"""

import os
from unidecode import unidecode
import dialogflow
from backend import hubapi
import wordcloudmaker
import random
import logging
from flask import jsonify
from datetime import datetime


class searchClass:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)  # sets up the logger
    logging.basicConfig(filename='ChatbotSearchClassLog.log', level=logging.INFO)  # declares level of # logging
    logging.info('---------------------------------')
    logging.info('Process at {}'.format(datetime.now()))
    # class which allows for multiple users to have a unique instance to avoid data bleeding across users
    textresponse = []
    location = []
    sentimentaim = []
    feature = []
    pricerange = []
    rating = []
    opinion_response = ''
    nearBy = []
    parameters_list = []
    empty_parameters = []
    filters_asked = []
    last_filter = []
    features_list = []
    number_hotels = 0
    hotel_found = []
    objectsession_id = ''
    session_id = ''

    def __init__(self, Sid):  # creation of instance
        self.name = Sid
        objectsession_id = Sid

    def detect_intent_texts(self, project_id, session_id, text, language_code):
        # detection for intents etc.
        session_client = dialogflow.SessionsClient()
        self.session_id = session_id
        # print(type(session_id))
        session = session_client.session_path(project_id, session_id)
        if text:
            text_input = dialogflow.types.TextInput(
                text=text, language_code=language_code)
            query_input = dialogflow.types.QueryInput(text=text_input)
            response = session_client.detect_intent(
                session=session, query_input=query_input)
            return response.query_result.fulfillment_text

    def handle_input(self, data):
        parameters = data['queryResult']['parameters']
        rest = parameters['rest'] if 'rest' in parameters else ''
        action = data['queryResult']['action']
        intent = ''
        response = ''
        intent = data['queryResult']['intent']['displayName']
        logging.info("INTENT: {}".format(intent))
        query = data['queryResult']
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(project_id, self.session_id)
        # store inputted data for processing
        # start with Intent checks
        print(intent)
        if intent == "Default Welcome Intent":  # if greeting detected, clear store values on instance
            self.location = ''
            self.feature = []
            self.pricerange = []
            self.rating = []
            self.nearBy = []
            self.sentimentaim = []
            self.opinion = False
            self.parameters_list = []
            self.opinion_response = ''

            response = data['queryResult']['fulfillmentText']
            for param in data['queryResult']['parameters']:
                if param != 'rest':
                    if param is list:
                        instanceDict[session_id].param = []
                    elif param is dict:
                        instanceDict[session_id].param = {}
                    elif param == 'opinion':
                        instanceDict[session_id].param = False
                    else:
                        instanceDict[session_id].param = ''
        elif intent == 'location':
            if 'city' in data['queryResult']['parameters']['location']:
                self.location = data['queryResult']['parameters']['location']['city']
            elif 'country' in data['queryResult']['parameters']['location']:
                self.location = data['queryResult']['parameters']['location']['country']
        elif intent == 'weatherlocation':
            if 'city' in data['queryResult']['parameters']['location']:
                location = data['queryResult']['parameters']['location']['city']
                output = self.weatherreport(location)
                response = output['weathersumup']
            else:
                response = "im sorry i don't recognise that city"
        elif intent == 'show opinions':
            if self.opinion_response != '':
                response = self.opinion_response

            elif 'features' in parameters and parameters['features'] != '': # if the user has specified a feature
                if 'sentimentaim' in parameters and parameters['sentimentaim'] != '':
                    response = 'ok what do you look for in a {} {}?'.format(parameters['sentimentaim'],
                                                                            parameters['features'])
                else:
                    response = 'ok what do you look for in {}'.format(parameters['features'])
            elif 'location' in parameters:  # if only the location is given do a generic sweep
                response = self.get_opinions(data, [], True)

        elif intent == 'show opinions - custom':
            print('searching for subwords !')
            if data['queryResult']['outputContexts'][0]['parameters']['location.original'] != '':
                data['queryResult']['parameters'] = data['queryResult']['outputContexts'][0]['parameters']
                response = self.get_opinions(data, [], True)
            else:
                response = "I'm sorry, where did you want to go?"
        elif intent == 'WeatherSearch':
            logging.info('finding places with your weather!')
            weatheraspect = data['queryResult']['parameters']['weatheraspects']
            response = hubapi.elasticweather(weatheraspect)
            if response == '':
                response = "Im sorry i couldn't find anywhere that was {}".format(weatheraspect)

        elif intent == 'ClearParameter':  # allows for clearing a specific value/list of values
            logging.info('clearing here')
            self.clearparam(data)  # removes the requested parameter
            hotel_found, query = hubapi.diag_elastic(self)  # re-queries
            response = self.searchoutput(hotel_found)  # outputs

        elif intent == 'AddParameter' or intent == 'MoreParameters - yes' or intent == 'MoreParameters - no':
            response = self.paramedit(intent, data)

        elif intent == "NoInfo":
            print("Couldn't see anything")

        elif intent == "NumberResultsFound":  # in case response count is too few
            answer1 = ['Yes, sorry, but I\'ll be able to offer you more soon.',
                       'For the moment yes, but I\'ll have more soon.', 'Yes, but I\'ll include more.']
            answer2 = ['So please tell me more about your search.',
                       'So please tell me more about what you would like to include.',
                       'So please tell me what I should consider for your hotel.']
            response = '<p>' + random.choice(answer1) + '</p>' + '<p>' + random.choice(answer2) + '</p>'
        elif intent == "SearchEnd":  # intent to ask for additional filters etc
            response = ""
            if self.number_hotels == 0:
                response += '<p>' + "I couldn't find any result. Can you modify the requirements?" + '</p>'
                response += self.finding_hotels(instanceDict[session_id].hotel_found, self.empty_parameters)
            else:
                response += self.finding_hotels(self.hotel_found, self.empty_parameters)
        elif intent == "Results":  # displays the results from question
            response = ""
            response = self.show_results(self.hotel_found, query)
        elif intent == "GoBackResults":  # allows going back from selection to showing all results
            response = '<p>' + "No problem, here is the list with all results:" + '</p>'
            response += self.show_results(self.hotel_found, query)
        elif intent == "BookHotel":  # allows for booking the hotel (displaying the html)
            logging.info("booking")
            if parameters['opinion']:
                opinion = True
            else:
                opinion = False
            response = self.booking_hotel(data, self.hotel_found, opinion)
        elif action == "searching":
            response = self.startsearching(data, rest)
        elif intent == 'features':  # in case features need adding/editing
            response = self.paramedit(self, intent, data)
        else:  # unknown intent seen, else statement to avoid crashing out
            print('UNKNOWN INTENT HELP!')
            logging.info('UNKNOWN INTENT HELP!')
        if rest != "" and rest != []:  # if there is any more text to send to dialogflwo
            text_input = dialogflow.types.TextInput(text=rest, language_code='en')
            query_input = dialogflow.types.QueryInput(text=text_input)
            resp = session_client.detect_intent(session=session, query_input=query_input)
            print("Parameters while rest not empty ", parameters)
            response = resp.query_result.fulfillment_text
        if response =='':
            response='Sorry i wasnt sure what to do with that sentence'
        reply = {
            "fulfillmentText": response
        }
        logging.info("REPLY: {}".format(reply))
        return jsonify(reply)

    # main object methods:

    def weatherreport(self, location):
        response = getWeather(location)
        return response

    def finding_hotels(self, hotel_found, empty_parameters):
        # method to check number of results and if additional filtration is needed
        response = ""
        number_hotels = len(hotel_found)
        logging.info("EMPTY PARAMETERS: ".format(empty_parameters))
        ask_filter = random.choice(empty_parameters)
        logging.info("ASK FILTER: ".format(ask_filter))
        last_filter = [ask_filter]
        logging.info("LAST FILTER: ".format(last_filter))
        if ask_filter not in self.filters_asked:
            self.filters_asked.append(ask_filter)
        logging.info("FILTERS ASKED: ".format(self.filters_asked))
        ask_nearby = ["Do you need it to be close to anything?", "Do you want the hotel close to anywhere?",
                      "Would you like it close to some specific place?", "Do you want it in any concrete location?"]
        ask_features = ["What about including any extra feature?", "Are there some features you'd prefer to have?",
                        "Is there any facility you would like to have?"]
        ask_price = ["How much are you willing to pay?", "Would you like to specify any price range?"]
        ask_rating = ["How should the hotel be rated?"]
        response += '<p>' + "I found " + str(number_hotels) + " results."
        if 0 < number_hotels <= 10:  # if # of results are 1-10 no additional filters needed
            response += " Do you want to see the results? If not, what else do you want to consider?"
            event.append({"name": "SHOWRESULTS", "languageCode": "en-US"})
        elif number_hotels > 10:  # if greater than 10 results, prompt for input
            if ask_filter == "nearBy":
                response += '</p>' + '<p>' + random.choice(ask_nearby)
            elif ask_filter == "features":
                response += '</p>' + '<p>' + random.choice(ask_features)
            elif ask_filter == "pricerange":
                response += '</p>' + '<p>' + random.choice(ask_price)
            elif ask_filter == "rating":
                response += '</p>' + '<p>' + random.choice(ask_rating)
        return response

    def show_results(self, hotel_found, query):
        # method for displaying results to user
        response = ""
        features = self.feature
        hotel_rating = self.rating
        hotel_pricerange = self.pricerange
        hotel_nearBy = self.nearBy
        number_hotels = len(hotel_found)

        for i in range(0, number_hotels):  # go through each result
            response += '<p>' + "HOTEL NAME: " + '<i>' + hotel_found[i][
                'hotel_name'] + '</i>' + "':  " + "   LOCALITY: " + hotel_found[i]['locality'] + "  "
            if features != []:
                response += "FEATURES: "
                for feature in features:
                    response += str(feature) + ' '
            if hotel_rating != []:
                response += "    RATING: " + hotel_found[i]['popular_rating']
            if hotel_pricerange != []:
                response += "     PRICE RANGE: " + str(hotel_found[i]['price_range_minimum']) + " - " + str(
                    hotel_found[i]['price_range_maximum'])
            if hotel_nearBy != [] and hotel_nearBy['place'] in query:
                response += "     NEAR BY: " + str(hotel_found[i]['nearby'])
            if hotel_found[i]['word_reviews'] != "":
                response += "     NUMBER REVIEWS: " + str(len(hotel_found[i]['word_reviews']))

        response += '</p>' + '<p>' + "Query: " + str(query) + '</p>'
        if number_hotels > 0:  # pick a hotel to generate a wordcloud on a particular hotel
            randomhotel = (random.randint(0, number_hotels)) - 1
            ('i chose number : {}'.format(randomhotel))
            temp = hotel_found[randomhotel]
            ('there are {} review available'.format(len(temp['word_reviews'])))
            if len(temp['word_reviews']) > 0:
                response += '<p> i made a worldcloud from all the reviews realating to the hotel: {} </p>'.format(
                    temp['hotel_name'])
                ('making word cloud of{}'.format(temp['hotel_name']))
                wordcloudmaker.makecloud(temp['id'])
                full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'hotel_review.png')
                render_template("index.html", user_image=full_filename)
        if number_hotels == 1:
            response += '<p>' + "Would you like to book this hotel?" '</p>'
        elif number_hotels > 1:
            response += '<p>' + "Which hotel would you like to book?" '</p>'
        return response

    def searchoutput(self, hotel_found):  # generates response text
        number_hotels = len(hotel_found)
        params = self.parameters_list
        response = ""
        ask_requirements = ["What else?", "Tell me any other requirement you would like to include in the search.",
                            "What else should I take into consideration?", "What else do you want to include?",
                            "What else do you want to add?", "What else should I consider?"]
        ask_location = ["Where did you want to go?",
                        "Im sorry, where did you want to go?",
                        "What country/city are you looking for?", "I need a destination please",
                        "What country/city were you considering?"]
        response += '<p>'
        response1 = ["Looking for a hotel"]
        for param in params:
            item_list = list(param.items())[0]
            logging.info('generating text: '.format(param))  # generates the query into a sentence
            if item_list[0] == 'location' and item_list[1]:
                if 'city' in item_list[1]:
                    response1.append("in {}".format(unidecode(item_list[1]['city'])))
                if 'country' in item_list[1]:
                    response1.append("in {}".format(item_list[1]['country']))
            if item_list[0] == 'features' and item_list[1]:
                if len(item_list[1]) > 1:
                    if ('with ' + item_list[1][0]) not in response1:
                        response1.append("with {}".format(item_list[1][0]))
                    for item in item_list[1]:
                        if 'with ' + item not in response1:
                            response1.append("with {}".format(item))
                else:
                    if ('with ' + item_list[1][0]) not in response1:
                        response1.append("with {}".format(item_list[1][0]))

            if item_list[0] == 'pricerange' and item_list[1] != '':
                if 'lower' in item_list[1] and \
                        'higher' not in item_list[1] or item_list[1]['higher'] == 0:
                    response1.append(
                        "costing more than {}".format(item_list[1]['lower']))
                elif 'higher' in item_list[1] and \
                        'lower' not in item_list[1] or item_list[1]['lower'] == 0:
                    response1.append(
                        "costing less than {}".format(item_list[1]['higher']))
                else:
                    response1.append(
                        "costing between {} and {}".format(item_list[1]['lower'],
                                                           item_list[1]['higher']))
            if item_list[0] == 'rating' and item_list[1]:
                response1.append("rated as {}".format(''.join(item_list[1])))

            if item_list[0] == 'nearBy' and item_list[1]:
                response1.append("close to {}".format(item_list[1]['place']))
        logging.info(response1)
        logging.info("RESPONSE: {} ".format(' '.join(response1)))  # displays final output sentence
        response += ' '.join(response1)
        if not self.location:
            response = random.choice(ask_location)
        else:  # generate no result response/ display results response
            response += '</p>'
            response += '<p>' + " I found " + str(number_hotels) + " hotels " + '</p>'
            if number_hotels == 0:
                response += '<p>' + "I couldn't find any result. Can you modify the requirements?" + '</p>'
            elif number_hotels > 0 and number_hotels <= 10:
                response += " Do you want to see the results? If not, what else do you want to consider?"
            else:
                response += '</p>'
                response += '<p>' + random.choice(ask_requirements) + '</p>'
        return response  # returns generated response

    def get_opinions(self, data, hotel_found, opinion):
        response = ''
        generic_features = ['food', 'room', 'staff', 'clean']
        polaritystrength = 0
        if opinion is True:
            string = False
            if 'selection' in data['queryResult']['parameters'] and data['queryResult']['parameters'][
                'selection'] != '':
                selection = data['queryResult']['parameters']['selection']
            elif 'numericSelect' in data['queryResult']['parameters'] and \
                    data['queryResult']['parameters']['numericSelect'] != '':
                selection = data['queryResult']['parameters']['numericSelect']
            else:
                selection = data['queryResult']['parameters']['location']
                string = True

            if data['queryResult']['parameters']['features'] != '':
                featuresearch = [data['queryResult']['parameters']['features']]
            else:
                featuresearch = generic_features
            # if feature and sub features exists, do review search
            if 'sentimentaim' in data['queryResult']['parameters'] and data['queryResult']['parameters'][
                'sentimentaim'] != '':
                aim = data['queryResult']['parameters']['sentimentaim']
                if aim == 'good':
                    polaritystrength = 70
                elif aim == 'ok':
                    polaritystrength = 50
                elif aim == 'poor':
                    polaritystrength = 30
                else:
                    polaritystrength = 60
            if 'Subfeatures' in data['queryResult']['parameters']:
                subwords = data['queryResult']['parameters']['Subfeatures']
            else:
                subwords = ''
            if string is False:  # prints out the users selected hotel url
                index = int(selection) - 1
                logging.info(str(featuresearch))
                print(generic_features)
                sentiment = get_sentiment(hotel_found[index]['locality'], featuresearch,
                                          self.hotel_found[index]['hotel_name'], subwords)
                index = self.hotel_found[index]['hotel_name']
            else:
                logging.info(featuresearch)
                sentiment = get_sentiment(selection, featuresearch, "", subwords)
                index = selection
            print(sentiment)
            # pause()
            score = get_matching_hotels(sentiment, polaritystrength)
            # print(score)
            logging.info(score)

            for hotel in score:
                for feature in score[hotel]:
                    # logging.info(feature, score[feature])
                    if score[hotel][feature]:
                        total = score[hotel][feature]['positive'] + score[hotel][feature]['negative'] + \
                                score[hotel][feature]['neutral']
                        pos = score[hotel][feature]['positive'] / total * 100
                        response += "<p> {}% of where the {} was mentioned ({} instances) were positive in {}. </p>" \
                            .format(int(pos), feature, total, hotel)
                if len(self.hotel_found) > 0:
                    response += "Here is the link to your selection: " \
                                + '<a href="%s" target="_blank" >%s</a> ''' % \
                                (self.hotel_found[0]['url'], self.hotel_found[0]['url'])
                self.opinion_response = response
        return response

    def booking_hotel(self, data, hotel_found, opinion):  # allows selection from hotels found list to display html link
        number_hotels = len(hotel_found)
        response = ''
        if opinion is True:
            response += self.get_opinions(data, hotel_found, opinion)
        if number_hotels == 1:  # if only result was gathered, display its ink
            if data['queryResult']['queryText'] == 'Show Opinions':
                response += self.opinion_response
            response += "Here is the link to your selection: " \
                        + '<a href="%s">%s</a> ''' % (hotel_found[0]['url'], hotel_found[0]['url'])
        else:  # check to see where user inputted a number/hotel name for seleciton
            if data['queryResult']['parameters']['selection'] != '':
                selection = data['queryResult']['parameters']['selection']
            else:
                selection = data['queryResult']['parameters']['numericSelect']
            name = data['queryResult']['parameters']['name']
            if selection != "":  # prints out the users selected hotel url
                index = int(selection) - 1
                response = "Here is the link to your selection: " \
                           + '<a href="%s">%s</a> ''' % (hotel_found[index]['url'], hotel_found[index]['url'])
            if name != "" and "last" not in name:
                for hotel in hotel_found:
                    if hotel['hotel_name'] == name:
                        response = "Here is the link to your selection: " \
                                   + '<a href="%s">%s</a> ''' % (hotel['url'], hotel['url'])
            if name != "" and "last" in name:
                response = "Here is the link to your selection: " \
                           + '<a href="%s">%s</a> ''' % (hotel_found[-1]['url'], hotel_found[-1]['url'])
        return response

    def startsearching(self, data, rest):  # begins inserting contents of sentence input into its object
        parameters = data['queryResult']['parameters']
        logging.info('at start searching: '.format(parameters))
        logging.info('comparison plist: '.format(self.parameters_list))
        # prints the input data and the data currently store in the object
        for param in parameters:
            found = False
            if param == 'location':  # overwrite location if user has typed in a new one
                for subitem in parameters[param]:
                    self.location = unidecode(parameters[param][subitem])
            if param != 'features':  # add any new features that have been requested into object
                for compparam in self.parameters_list:
                    if compparam != []:
                        if param == (list(compparam.items())[0])[0] and parameters[param] != '':
                            found = True
                            self.parameters_list.remove(compparam)
                            self.parameters_list.append({param: parameters[param]})
            if found is False and parameters[param] != '':  # add anything thats new into object
                self.parameters_list.append({param: parameters[param]})
        if rest == "":  # whole sentence has been processed
            #  stores the respective values in the objects respective attribute
            # goes through gathered parameters within the object and stores them just incase
            logging.info("Parameters when rest empty: ".format(parameters))
            for elem in self.parameters_list:
                if 'location' in elem and elem['location'] != "":
                    for word in elem['location']:
                        elem['location'][word] = unidecode(elem['location'][word])
                    hotel_location = elem['location']
                    self.location = hotel_location
                if 'features' in elem and elem['features'] != "":
                    features = elem['features']
                    for featureitem in features:
                        if featureitem not in self.feature:
                            self.feature.append(featureitem)
                if 'pricerange' in elem and elem['pricerange'] != "":
                    if 'pricerange' in data['queryResult']['parameters']:
                        if (len(self.pricerange)) == 0:
                            if 'pricerange' not in self.pricerange:
                                self.pricerange = []
                                temp = {
                                    'higher': 0,
                                    'lower': 0
                                }
                                tempprice = {
                                    'pricerange': temp
                                }

                                self.pricerange.append(tempprice)
                        if 'higher' in self.pricerange[0]['pricerange'] and 'higher' in \
                                data['queryResult']['parameters']['pricerange'] and \
                                data['queryResult']['parameters']['pricerange']['higher'] != 0:

                            self.pricerange[0]['pricerange'].update(data['queryResult']['parameters']['pricerange'])
                        elif 'lower' in self.pricerange[0]['pricerange'] and 'lower' in \
                                data['queryResult']['parameters']['pricerange'] and \
                                data['queryResult']['parameters']['pricerange']['lower'] != 0:

                            self.pricerange[0]['pricerange'].update(data['queryResult']['parameters']['pricerange'])
                    else:
                        self.pricerange.append(elem)

                if 'rating' in elem and elem['rating'] != "":
                    hotel_rating = elem['rating']
                    self.rating.append(hotel_rating)

                if 'nearBy' in elem and elem['nearBy'] != "":
                    hotel_nearBy = elem['nearBy']
                    self.nearBy.append(hotel_nearBy)

                if 'sentimentaim' in elem and elem['sentimentaim'] != "":
                    sentimentaim = elem['sentimentaim']
                    self.sentimentaim.append(sentimentaim)

        logging.info("LOCATION: ".format(self.location))
        logging.info("FEATURES: ".format(self.feature))
        logging.info("PRICERANGE: ".format(self.pricerange))
        logging.info("RATING: ".format(self.rating))
        logging.info("NEARBY: ".format(self.nearBy))
        logging.info("SENTIMENT: ".format(self.sentimentaim))
        logging.info("/*** PARAMS: ".format(parameters))
        for param in parameters:
            if param == 'features' and not data['queryResult']['parameters'][param] \
                    and param not in self.empty_parameters:
                self.empty_parameters.append(param)
            if param != "currency-name" and param != "rest" and param != 'location' and param != 'parameter' and \
                    param not in self.empty_parameters and param in data['queryResult']['parameters'] and \
                    data['queryResult']['parameters'][param] == "":
                self.empty_parameters.append(param)
        if self.location:
            ### results from Elasticsearch
            hotel_found, query = hubapi.diag_elastic(self)
        else:
            hotel_found = []
        response = self.searchoutput(hotel_found)
        self.hotel_found = hotel_found
        print(response)
        return response

    def clearparam(self, data):  # process of removing an element or whole segment of elements
        connectives = ['and', ',', ', ']
        parameters = self.parameters_list
        rest = data['queryResult']['parameters']['rest']
        # replace possible words with the actual parameter
        clear = data['queryResult']['parameters']['clear']
        # logging.info("clearing ", str(clear))
        if clear == 'feature':  # if the clear request is just a parameter name, empty the entire field
            clear = 'features'
        elif clear == 'price' or clear == 'price range':
            clear = 'pricerange'
        elif 'rating' in clear or 'rated' in clear:
            clear = 'rating'
        elif clear == 'nearby' or clear == 'near by' or clear == 'place':
            clear = 'nearBy'
        print("start list ", parameters)

        for param in parameters:  # check to see if clear request was a specific element value
            if list(param.items())[0][1] != "":
                if list(param.items())[0][0] == 'features' and (list(param.items())[0])[1][0] and \
                        (list(param.items())[0])[1][0] == clear:
                    list(param.items())[0][1].remove(clear)
                elif len(list(param.items())[0][1]) > 0:
                    for item in list(param.items())[0][1]:
                        if clear == item:
                            pos = list(param.items())[0][1].index(clear)
                            (list(param.items())[0][1].pop(pos))
                if list(param.items())[0][0] == 'pricerange' and param.items()[0][1] == clear:
                    parameters[param] = []
                if list(param.items())[0][0] == 'rating' and param.items()[0][1] == clear:
                    parameters[param] = []
                if list(param.items())[0][0] == 'nearBy' and param.items()[0][1] == clear:
                    parameters[param] = []
        print("cleared list ", parameters)  # show list of elements removed
        if rest != '':
            temp = rest.split()
            if temp[0] in connectives:
                temp[0] = temp[0] + 'remove '
            else:
                for item in parameters:
                    if temp[0] in parameters[item]:
                        temp[0] = 'remove ' + temp[0]
            rest = ' '.join(temp)
        print('changed rest: ', rest)

    def paramedit(self, intent, data):  # if user simply requested to add something to a particular field
        if intent == "AddParameter":  # 'user said i want to add a feature'
            parameter = data['queryResult']['parameters']['parameter']
            if parameter == 'features':
                response = "What features?"
            if parameter == 'pricerange':
                response = "What price range?"
            if parameter == 'rating':
                response = "What rating?"
            if parameter == 'nearBy':
                response = "Close to where?"
        if intent == "MoreParameters - no":  # if user doesnt want to add anything extra
            response = ""
            print("empty parameters ", self.empty_parameters)
            print("filters_asked ", self.filters_asked)
            for filter in self.filters_asked:  # removes a filter if we have data on it now
                if filter in self.empty_parameters:
                    self.empty_parameters.remove(filter)
            # process new input
            if self.empty_parameters:
                response += self.finding_hotels(self.hotel_found, self.empty_parameters)
            else:
                response += self.searchoutput(data, self.hotel_found)
        if intent == "MoreParameters - yes":
            logging.info("add more")  # user wants to add more elements
            logging.info("filters_asked: ".format(self.filters_asked))
            filter = self.filters_asked[-1]
            logging.info(" LAST FILTER: ".format(self.last_filter))
            if filter in self.empty_parameters:  # check to see whats not been added and ask about it
                if filter == 'features':
                    response = "What features?"
                if filter == 'pricerange':
                    response = "What price range?"
                if filter == 'rating':
                    response = "What rating?"
                if filter == 'nearBy':
                    response = "Close to where?"
                    self.empty_parameters.remove(filter)
        return response
