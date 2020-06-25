import os
import sys
import requests    
from flask import jsonify, request, make_response, send_from_directory
from flask_cors import CORS
import numpy as np
import pandas as pd
import holoviews as hv
from holoviews import dim, opts
import bokeh
from bokeh.document import Document
from bson.json_util import dumps, loads
import pymongo
import strax
import straxen
import json
from context import xenon1t_dali
from holoviews_waveform_display import waveform_display
hv.extension("bokeh")

# # Read live data
# Load data
st_low = xenon1t_dali(output_folder='./strax_data', build_lowlevel=True)
st_high = xenon1t_dali(output_folder='./strax_data', build_lowlevel=False)
runs_low = st_low.select_runs()
runs_high = st_high.select_runs()
available_runs = runs_low['name']
renderer = hv.renderer('bokeh')
print("renderer created: ", renderer)

# Connect to MongoDB
APP_DB_URI = "mongodb+srv://char_dev:2Qz2o5Kh8agcVrXB@cluster0-oumsb.mongodb.net/waveform?retryWrites=true&w=majority"
my_db = pymongo.MongoClient(APP_DB_URI)["waveform"]
my_auth = my_db["auth"]
my_app = my_db["app"]

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
os.environ.update({'ROOT PATH' : ROOT_PATH})
sys.path.append(os.path.join(ROOT_PATH, 'modules'))

import logger 
from app import app
CORS(app, supports_credentials=True) # Supports authenticated request

#Create a logger object for info and debug
LOG = logger.get_root_logger(os.environ.get(
    'ROOT_LOGGER', 'root'), filename = os.path.join(ROOT_PATH, 'output.log'))

PORT = 4000 
# os.environ.get('PORT')

def authenticate():
    def wrapped():
        return
    return

@app.errorhandler(404)
def not_found(error):
    """error handler"""
    LOG.error(error)
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/')
def index():
    """static files server"""
    return send_from_directory('dist', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    file_name = path.split('/')[-1]
    dir_name = path.join('dist', '/'.join(path.split('/')[:-1]))
    return send_from_directory(dir_name, file_name)

@app.route('/api/data')
def send_data():
    print(request.cookies)
    user = request.args.get('user')
    print(user)
    document = my_app.find_one({'user': user})
    # print(document)
    if (document == None):
        print("does not have record for the user: ", user)
        post = {'user': user,                 
                "run_id": "",
                "build_low_level": True,
                "bokeh_model": None,
                "tags_data": []}
        document = my_app.insert_one(post)
    document["available_runs"] = available_runs
    json_str = dumps(document)
    return make_response(json_str, 200)


@app.route('/api/gw',  methods = ['POST'])
def get_waveform():
    if request.is_json:
        req = request.get_json()
        print(req)
        run_id = req["run_id"]
        build_low_level = req["build_low_level"]
        user = req["user"]   
        plot = None         
        if build_low_level:
            df = st_low.get_array(run_id, "event_info")
            event = df[4]
            print(event)
            plot = waveform_display(context = st_low, run_id = str(run_id), time_within=event)
        else:
            df = st_high.get_array(run_id, "event_info")
            event = df[4]
            print(event)
            plot = waveform_display(context = st_high, run_id = str(run_id), time_within=event)
        
        # A container for Bokeh Models to be reflected to the client side BokehJS library.
        bokeh_document = renderer.server_doc(plot)
        print("converted to doc: ", bokeh_document)

        bokeh_model = bokeh_document.roots[0]
        bokeh_model_json = bokeh.embed.json_item(bokeh_model)        
        # Update database
        mongo_document = my_app.find_one({"user": user})
        if (mongo_document):
            my_app.update_one({"user": user}, 
            {"$set": { 
                "run_id": run_id, 
                "build_low_level" : build_low_level,
                "bokeh_model": bokeh_model_json,
                }
            }
            )
        else:
            post = {
                "user": user,
                "run_id": run_id,
                "build_low_level": build_low_level,
                "bokeh_model": bokeh_model_json,
                "tags_data": [],
                }
            my_app.insert_one(post)
        return json.dumps(bokeh_model_json)

    else:
        return make_response(jsonify({"success": False}), 400)

@app.route('/api/sw',  methods = ['POST'])
def save_waveform():
    if request.is_json:
        req = request.get_json()
        print(req["user"], req["tag"], req["comments"], req["build_low_level"], req["run_id"])
        user = req["user"]  
        tag = req["tag"]
        comments = req["comments"]
        build_low_level = req["build_low_level"]
        run_id = req["run_id"]
        bokeh_model = req["bokeh_model"]
        # Update database
        my_app.update_one({"user": user}, 
            {"$set": { 
                "run_id": run_id, 
                "build_low_level" : build_low_level,
                "bokeh_model": bokeh_model,
                }
            }
        )
        mongo_document = my_app.find_one({"user": user, "tags_data."+tag: {"$exists": True}})
        if (mongo_document):
            print("mongo document found: ")

            my_app.update_one({"user": user, "tags_data."+tag: {"$exists": True}}, 
                {"$set": { 
                        "tags_data.$."+tag+".comments": comments,
                        "tags_data.$."+tag+".run_id": run_id,
                        "tags_data.$."+tag+".build_low_level": build_low_level,
                        "tags_data.$."+tag+".bokeh_model": bokeh_model
                    }
                }
            )
        else:
            mongo_document = my_app.find_one({"user": user})
            my_app.update_one({"user": user},
                {
                    "$push": {
                        "tags_data": {
                            tag: {
                                "run_id": run_id,
                                "build_low_level": build_low_level,
                                "comments": comments,
                                "bokeh_model": bokeh_model,
                            }
                        }
                    }
                }
            )
        return make_response(jsonify({"success": True}), 200)
    else:
        return make_response(jsonify({"success": False}), 400)



if __name__ == "__main__":
    # LOG.info('running environment: %s', os.environ.get('ENV'))
    app.config['DEBUG'] = os.environ.get('ENV') == 'development' #debug mode
    app.run(host = '0.0.0.0', port = int(PORT)) # Run the app