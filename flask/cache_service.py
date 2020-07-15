import pickle
import threading
from threading import Thread
import os
from bson.binary import Binary
import straxen
import holoviews as hv
import pymongo
import datetime
import time
import bokeh
from holoviews_waveform_display import waveform_display

# Bokeh backend setup
hv.extension("bokeh")
renderer = hv.renderer('bokeh') # Bokeh Server
lock = threading.Lock() # A Lock to address race condition

# Get the number of processors/cores available in the system
cpu_count = os.cpu_count()
print("Number of processors/cores available in the system: ", cpu_count)

APP_DB_URI = os.environ.get("APP_DB_URI", None)
if (APP_DB_URI == None):
    print("MongoDB Connection String Not Set")
my_db = pymongo.MongoClient(APP_DB_URI)["waveform"]
my_request = my_db["request"]
my_waveform = my_db["waveform"]
st = straxen.contexts.xenon1t_dali()

def load_data(run_id, event_id):
    df = st.get_array(run_id, "event_info")
    event = df[int(event_id)]
    waveform = waveform_display(context=st, run_id=run_id, time_within=event)
    lock.acquire()
    try:
        waveform = renderer.server_doc(waveform).roots[-1]
    finally:
        lock.release()
    waveform = bokeh.embed.json_item(waveform)
    return waveform

def cache_data(run_id, event_id, waveform, msg):
    post = {"event_id" : event_id, "run_id" : run_id, "waveform": waveform, "msg": msg}
    document = my_waveform.find_one(post)
    if (document == None):
        my_waveform.insert_one(post)

def fetch_request():
    while True:
        document = my_request.find_one_and_update({"status": "new"}, 
                                                  {"$set" : {"status": "use"}})
        while (document):
            event_id = document["event_id"]
            run_id = document["run_id"]
            try:
                waveform = load_data(run_id, event_id)
                cache_data(run_id, event_id, waveform, "")
            except Exception as e:
                print("An exception occured ", e)
                if hasattr(e, "message"):
                    cache_data(run_id, event_id, None, e.message)
                else:
                    cache_data(run_id, event_id, None, "Data Not Available")
            my_request.find_one_and_update({"status": "use", "event_id": event_id, "run_id": run_id}, 
                                           {"$set" : {"status": "old"}})
            print("Just cached the run ", run_id, "and event ", event_id)
            document = my_request.find_one_and_update({"status": "new"}, 
                                                      {"$set" : {"status": "use"}})
        # Sleep the app if no new requests
        time.sleep(10)

if __name__ == "__main__":
    print("Service starts now: ", datetime.datetime.now())
    threads = []
    start_time = datetime.datetime.now()
    for i in range(0, min(8, cpu_count)):
        t = Thread(target=fetch_request, daemon=True)
        threads.append(t)
        t.start()
    # Main thread sleeps for 1 hour and terminates
    # Daemonic threads are terminated automatically
    time.sleep(60 * 60)