import pandas as pd
import numpy as np

# visualization
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# machine learning
# from sklearn.linear_model import Perceptron
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from keras.models import Sequential
from keras.layers import Dense
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
import requests
import json
import pandas as pd
import numpy as np
import geopy
from geopy import distance
import datetime
import math
import itertools
import openrouteservice
from openrouteservice import convert
import folium
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import matplotlib.pyplot as plt
from folium.plugins import FastMarkerCluster
from geopy import distance

client = openrouteservice.Client(key='5b3ce3597851110001cf6248a0d5fffbf696486096ec44ccf2e406b9')
locator = Nominatim(user_agent="EnergyPrediction")
drop_names = ['longitude','latitude', 'elevation', 'distance(m)', 'duration(s)', 'Delta_Vel^2']

class EnergyPred:
    modelParamFileName = ""
    homeGPS = None

    @staticmethod
    def init(homeGPS):
        EnergyPred.homeGPS = homeGPS

    @staticmethod
    def norm(x):
        train_stat = x.describe()
        train_stat = train_stat.transpose()
        norm_value = (x - train_stat['mean']) / train_stat['std']
        return norm_value
        
    @staticmethod
    def standardize(raw_data):
        stand_data = (raw_data - np.mean(raw_data, axis = 0)) / np.std(raw_data, axis = 0)
        return stand_data

    @staticmethod
    def data_process(df):
        trail_copy = df.copy()
        trail_copy['acceleration(m/s^2)'] = np.insert(np.diff(trail_copy['velocity(m/s)']) / np.diff(trail_copy['distance(m)']),0,0.0)
        trail_copy["Delta_Vel^2"] = np.insert(np.diff(np.square(trail_copy['velocity(m/s)'])),0,0.0)
        trail_copy['acceleration(m/s^2)'].fillna(trail_copy['acceleration(m/s^2)'].median(), inplace = True)
        trail_copy.drop(trail_copy.index[trail_copy['acceleration(m/s^2)'] == np.inf], inplace=True)
        trail_copy["STDDis"] = EnergyPred.standardize(trail_copy["distance(m)"])
        trail_copy["STDDV"] = EnergyPred.standardize(trail_copy["Delta_Vel^2"])
        trail_copy["STDH"] = EnergyPred.standardize(trail_copy["elevation"])
        # self.trail_data = trail_copy
        return trail_copy
        
    
    # def storeData(self, fileName):
    #     data = [self.trail_data]
    #     jdata = json.dumps(data)
    #     with open(fileName, 'w+') as file:
    #         file.write(jdata)

    # @staticmethod
    # def loadData(fileName):
    #     dataset = pd.read_json(fileName)
    #     trail_NN = dataset.drop(drop_names, axis=1)
    #     train, test = train_test_split(trail_NN, shuffle=True, test_size=0.2, random_state=0)
    #     x_train, y_train = train.drop('soc consumtion(%)', axis=1), train['soc consumtion(%)']
    #     x_test, y_test = test.drop('soc consumtion(%)', axis=1), test['soc consumtion(%)']
    #     normed_train_data0 = EnergyPred.norm(x_train)
    
    
    # def learn(x_training):
    #
    #     model = keras.Sequential([
    #         layers.Dense(64, activation='relu', input_shape=[len(x_training.keys())]),
    #         layers.Dense(64, activation='relu'),
    #         layers.Dense(1)
    #         ])
    #     optimizer = tf.keras.optimizers.RMSprop(0.001)
    #
    #     model.compile(loss='mse',
    #                   optimizer=optimizer,
    #                   metrics=['mae', 'mse'])
    #
    #     return model

    # @staticmethod
    # def store(x_training, y_training, norm_x, model, EPOCHS):
    #     model = EnergyPred.learn(EnergyPred.x_train)
    #     model.fit(EnergyPred.normed_train_data0, EnergyPred.y_train, epochs=EPOCHS, validation_split = 0.2, verbose=0)
    #     model.save("NNmodel")

    @staticmethod
    def load():
        recall_model = keras.models.load_model("NNmodel")
    @staticmethod
    def vel_slope(df, dist, dur):
        res = []
        slope = []
        for i, j in zip(dist, dur):
            try:
                res.append(i / j)
            except ZeroDivisionError:
                res.append(0.0)
    
        for i in range(len(df['elevation'])):
            if i >= 1:
                y = df['elevation'][i]-df['elevation'][i-1]
                x = dist[i-1]
                if x == 0:
                    slope.append(0.0)
                elif y == 0:
                    slope.append(0.0)
                else:
                    slope.append(round(y / x, 5))
        df['velocity(m/s)'] = res
        df['slope'] = slope
        return df
        
        
    @staticmethod
    def predict(lat, lng):
        # Route Found
        coord = [[EnergyPred.homeGPS[1], EnergyPred.homeGPS[0]], [lng, lat]]
        route = client.directions(coordinates=coord,
                          profile='driving-car',
                          format='geojson',
                          validate=False,)
        
        # Elevation Get
        coord0 = route['features'][0]['geometry']['coordinates']
        route_elevation = client.elevation_line(format_in='polyline',  
                                                format_out='geojson',
                                                geometry=coord0,)
        
        gps_points = pd.DataFrame(route_elevation['geometry']['coordinates'], 
                                  columns = ['longitude', 'latitude', 'elevation'])
        
        # Distance/Duration Get
        distance_cal = [0.0]
        duration_cal = [0.0]
        iter_a, iter_b = gps_points.shape
        check_iter = iter_a - 1
        for i in range(check_iter):
            d = distance.distance((gps_points.loc[i, "latitude"], gps_points.loc[i, "longitude"]), 
                                  (gps_points.loc[i+1, "latitude"], gps_points.loc[i+1, "longitude"]))
            distance_cal.append(d.km)
            sub_coord = [[gps_points.loc[i, "longitude"], gps_points.loc[i, "latitude"]], 
                     [gps_points.loc[i+1, "longitude"], gps_points.loc[i+1, "latitude"]]]
            sub_route = client.directions(coordinates=sub_coord,
                                          profile='driving-car',
                                          format='geojson',
                                          validate=False,)
            sub_dur = sub_route['features'][0]['properties']['segments'][0]['duration']
            duration_cal.append(sub_dur)
        
        # X-Data Cleaning
        new_df = EnergyPred.vel_slope(gps_points, distance_cal, duration_cal)
        df_clean = EnergyPred.data_process(new_df)
        X_data = df_clean.drop(drop_names, axis=1)
        norm_x_data = EnergyPred.norm(X_data)
        y_pred = EnergyPred.recall_model.predict(norm_x_data)
        soc_consump_predict = np.sum(y_pred)
        return soc_consump_predict