"""
Description:    Query data in elasticsearch
Author:     Callum Williams - SpinningBytes
"""

from elasticsearch import Elasticsearch
import logging
from elasticsearch_dsl import Search,Q

import json


def diag_elastic(filename):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename='queryLog.log', level=logging.INFO)
    logging.info('---------------------------------')
    logging.info('WOO im here to query!')
    # extract search parameters - main interaction with diaglog flow
    with open(filename, encoding='utf-8')as f:  # load up response file that arrived from diaglogflow
        d = json.load(f)
        logging.info('loaded Json')
        i = 0
        data = {}
        for item in d['queryResult']['parameters']:  # for every search parameter
           # print(item)
            if 'amenity' in item:  # if its an amenity, number it
                i += 1
                location = 'amenity' + str(i)
            else:
                location = item

            data.update({  # add param to dict
                location: d['queryResult']['parameters'][item]
            })
        logging.info(data)
    logging.info('building query')
    #  main interaction with elastic search
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    res = Search(using=es, index='chatbotdata', doc_type='docket')
    idx = 0
    badparams = []
    location=False
    moneyfound=False
    nearbyrequest=[]


    res = res.query("match", locality=data['geo-city'])
    logging.info("looking for hotels in {} ".format(data['geo-city']))
    for param in data:
        if param == 'rating' and not data['rating'] == '':
            res = res.query('match', popular_rating=data['rating'])
            logging.info("looking for hotels with a rating of  {} ".format(data[param]))

        elif 'amenity' in param and not data[param] == '':
            idx += 1
            logging.info("looking for hotels with {} ".format(data[param]))
            res = res.query("match", amenities=data['amenity'+str(idx)])

        elif param == 'pricerange':
            if 'higher' in data['pricerange']:
                if data[param]['higher'] == '':
                    temphigher = 9999
                else:
                    temphigher=data[param]['higher']
            else:
                temphigher = 9999

            if 'lower' in data['pricerange']:
                if data[param]['lower'] == '':
                    templower = 0
                else:
                    templower=data[param]['lower']
            else:
                templower = 0

            # checks if elements are present, if existing and blank then default values

            if 'higher' in data[param]:# existence check
                if 'lower' in data[param]:# existence check
                    logging.info("looking for hotels below the price of {} ".format(temphigher))
                    logging.info("looking for hotels above the price of {} ".format(templower))
                    res = res.query('range', price_range_maximum={'lte':temphigher})
                    res = res.query('range', price_range_minimum={'gte': templower})
                    moneyfound = True
                else:
                    res = res.query('range', price_range_maximum={'lte':temphigher})
                    logging.info("looking for hotels below the price of {} ".format(temphigher))
                    moneyfound = True
            elif 'lower' in data[param]:# existence check
                logging.info("looking for hotels above the price of {} ".format(templower))
                res = res.query('range', price_range_minimum={'gte': templower})
                moneyfound = True
            else:
                logging.info("we have no price range to search with")

        elif param == 'nearBy' and not data[param] == '':
                location = True
                if isinstance(data[param]['place'],str):
                    nearbyrequest.append(data[param]['place'])
                elif len(data[param]['place'])>1:
                    for item in data[param]['place']:
                        nearbyrequest.append(item)
        else:
            if data[param] != 'geo-city':
                logging.info("object not found "+data[param])
                badparams.append(param)
    for badele in badparams:
        del data[badele]
        logging.info("object {} removed ".format(badele))
    # this has to be done somewhat hardcoded due to labels i.e'locality' needing to be explicitly called
    query = res.query._proxied._params    # store query
    total = res.count()  # gets total number of results that matched criteria



    locresponse=[]
    if location is True:
        locres = Search(using=es, index='locationdata', doc_type='docket')
        for request in nearbyrequest:
            locres = locres.filter("match", location=request.lower())
        loctotal=locres.count()

        locresponse = locres[0:loctotal].execute()
    result = []
    locationquery = False
    if total > 0:
        for hit in res.scan():
            if locresponse:
                locationquery=True
                for lochit in locresponse:
                    if lochit['hotel_url'] == hit['url']:
                        temp = hit.to_dict()
                        if temp not in result:
                            result.append(temp)
            else:
                temp = hit.to_dict()
                if temp not in result:
                    if moneyfound is True:
                        if temp['price_range_maximum'] <=temphigher and temp['price_range_minimum']>=templower:
                            result.append(temp)
                    else:
                        result.append(temp)
    else:
        logging.info("\n im sorry i couldn't find anything that matched your criteria, try again with fewer requirements")

    if locationquery is True:
        locquery = locres.query._proxied._params
        temp1=str(locquery)
        temp2=str(query)
        temp3=temp2+' '+temp1
        logging.info('\nI found {} results that matched your criteria\nWith query {} and location query {}'.format(len(result), query, locquery))

    else:
        logging.info('\nI found {} results that matched your criteria\nWith query {}'.format(len(result), query))
        temp3=str(query)
    result.append(temp3)


    with open('elasticsearch_query_results.json', 'w', encoding='utf8')as datasetfile:
         json.dump(result, datasetfile, indent=4, ensure_ascii=False)
    # in case result needs to sent to file

    return result
# here is where the interaction with the web page will take place
if __name__ == '__main__':
    print(diag_elastic('dialogflow_response_test.json'))
