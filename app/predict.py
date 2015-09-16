from bitmicro.model import features as f
import pymongo
import time
import sys
import pickle
import numpy as np

client = pymongo.MongoClient()
db = client['bitmicro']
symbol = sys.argv[1]
duration = int(sys.argv[2])
threshold = float(sys.argv[3])
predictions = db[symbol+'_predictions']

with open('cols.pkl', 'r') as file1:
    cols = pickle.load(file1)
with open('model.pkl', 'r') as file2:
    model = pickle.load(file2)

print 'Running...'
active = False
trade_time = 0
while True:
    start = time.time()
    position = 0
    try:
        data = f.make_features(symbol,
                               1,
                               [duration],
                               [30, 60, 120, 180],
                               [2, 4, 8],
                               True)
        pred = model.predict(data[cols].values)[0]
    except Exception as e:
        print e
        sys.exc_clear()
    else:
        if data.width.iloc[0] > 0:
            if active:
                if start - trade_time >= 30:
                    active = False
            elif abs(pred) > threshold:
                active = True
                trade_time = time.time()
                position = np.sign(pred)
            current_price = data.pop('mid').iloc[0]
            entry = {'prediction': pred,
                     'current_price': current_price,
                     'future_price': 0,
                     'position': position}
            predictions.update_one({'_id': data.index[0]},
                                   {'$setOnInsert': entry},
                                   upsert=True)
            predictions.update_many({'_id': {'$gt': start-duration-.5,
                                             '$lt': start-duration+.5}},
                                    {'$set': {'future_price': current_price}})
    time_delta = time.time()-start
    if time_delta < 1.0:
        time.sleep(1-time_delta)
