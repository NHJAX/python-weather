#WBGT Calculator and Weather Forcaster
#Created by Kevin Nichols and Alex Rangeo
#WEB GUI Created by Marvin Andara Vargas
#Vista Defense, Concept Plus
#Feb 2019

#import LIB
from math import exp,expm1
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.http import http_date
import Adafruit_DHT
import statistics
import pytz
import pymetar
import paho.mqtt.client as mqtt
import json
import time
from weatheralerts import WeatherAlerts
from io import StringIO
import sys

#init MQTT broker path
SERVER = '76.122.12.92' #public address of MQTT broker
CLIENT_ID = 'JAX_SENSOR' #name of MQTT client "use a naming conventation ie. LOCATION_SENSOR"
TOPIC = 'jax' #Topic under which to publish the data
client = mqtt.Client(CLIENT_ID, SERVER) #settings concated
client.connect("76.122.12.92", 1883)   # Connect to MQTT brokerclient

#create instance of flask and cors
app = Flask(__name__)
CORS(app)

#to inifinity and beyond
while True: #will run forever
        
#set PYMETAR AWOS Station
    station = "KNIP" #change this based on location of RPI Weather Station

#Parse Metar
    rf = pymetar.ReportFetcher(station)
    re = rf.FetchReport()
    rp = pymetar.ReportParser()
    pr = rp.ParseReport(re)
#Gather Sensor data

    #From PI
    humidityleft, temperatureleft = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4) #DHT11 is the sensor, 4$
    humidityright, temperatureright = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 22) #DHT11 is the sensor$

    #From AWOS
    W = pr.getWindSpeedMilesPerHour() #get request for winds in MPH
    P = pr.getPressure() #get request for pressure
    L = "NAS JAX" #change this based on location of RPI Weather Station
    
#concate humidity and temperature integer from four variables to two
    h = (humidityleft, humidityright) #takes the humidity from both sensors and calculates the average
    t = (temperatureleft, temperatureright) #takes the temperature from both sensros and calculates the av$

#average humidity and temperature from two DHT11 sensors
    humidity = statistics.mean(h)
    c = statistics.mean(t)

#convert winds to meters per second
    winds = W/2.237#divide speed value by 2.237
    
#Convert Temperature to Fahrenheit
    temp  = (c * 1.8) + 32
    tempL = (temperatureleft * 1.8) + 32
    tempR = (temperatureright * 1.8) + 32

#calculate WBGT
    relative = exp(17.27*c/(237.7+c))
    vapor = humidity/100*winds*relative
    wbgtc = 0.567*c+0.393*vapor+3.94
    wbgtf  = (wbgtc * 1.8) + 32

#convert Floats to Integers
    temperature = round(temp,1)
    Pres = round(P, None)
    WBGTC = round(wbgtc,None)
    WBGTF = round(wbgtf,None)
 
#Flag Color
    if (wbgtf < 80):
        flag = 'green'
    if (wbgtf > 80) and (wbgtf < 84.9):
        flag = 'green'
    if (wbgtf > 85) and (wbgtf < 87.9):
        flag = 'yellow'
    if (wbgtf > 88) and (wbgtf < 89.9):
        flag = 'red'
    if (wbgtf > 90):
        flag = 'black'

#get Weather Alerts for duval county
    nws = WeatherAlerts(state='FL' , samecodes=['012031']) #duval county
    list = [] #inits list
    for alert in nws.alerts: #loopadoop
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        print (alert.title)
        sys.stdout = old_stdout
        str_a = mystdout.getvalue()
        str_b = str_a.strip()
        list.extend([str_b])

    wwa = list
   
#build message as JSON dump
    json_map = {"location": L, "WarnWatchAdvise": wwa, "humidity": humidity, "temperature": temperature, "winds": W, "pressure": Pres, "wbgt": WBGTF, "flagColor": flag, "AWOS": {"windDirection": pr.getWindDirection(), "windSpeed": pr.getWindSpeedMilesPerHour(), "temperature": pr.getTemperatureFahrenheit(), "weatherCon": pr.getWeather()}}

#JSON onject compiled
    msg = json.dumps(json_map) 

   #test output debug
    #completed Formatted JSON objects prints to HDMI out
    print(msg)
   
#nap time
    time.sleep(4)
    #aint nobody got time for that
    
#publish to MQTT broker    
    client.publish(TOPIC, msg)



