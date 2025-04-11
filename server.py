from ast import While
from dataclasses import dataclass
from email import header
from paho.mqtt import client as mqtt_client
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv, find_dotenv

import requests
import json
import hashlib
import random
import time
import os

print ("Starting program")

#load .env variables
load_dotenv()

USERNAME = os.getenv('USERNAME', "")
USERPASSWORD = os.getenv('USERPASSWORD',"")
MQTT_HOST_ADDRESS = os.getenv('MQTT_HOST_ADDRESS',"")
MQTT_USERNAME = os.getenv('MQTT_USERNAME',"")
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD',"")
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
API_FREQUENCY_CHECK = int(os.getenv('API_FREQUENCY_CHECK',900))

print ("Using MQTT Server: " + MQTT_HOST_ADDRESS)
print ("On port: " + str(MQTT_PORT))
print ("Checking every " + str(API_FREQUENCY_CHECK) + " seconds for new data from Hoymiles")
print ("Checking now...")

class Energy:
    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(bytes(password,"utf-8")).hexdigest()
        self.today = ""
        self.this_month = ""
        self.this_year = ""
        self.lifetime_energy = ""
        self.current_power = ""
        self.last_update = ""
        self.authorizationheader = self.authentication_header() 
        self.update()

    def authentication_header(self):
        print ()
        response_auth = json.loads(requests.post("https://neapi.hoymiles.com/iam/pub/0/auth/login", json={'user_name': self.username, 'password': self.password}).text)
        token = response_auth["data"]["token"]
        headers = {"Authorization": token}
        self.cookie = headers
        print ("Authentication token received!")
        return headers

    def get_sid(self):
        response = json.loads(requests.post("https://neapi.hoymiles.com/pvm/api/0/station/select_by_page", headers=self.authorizationheader, json={'page': 1, 'page_size': 2}).text)
        
        if response["message"] == "success":
            site_list = response["data"]["list"]
            site_dict = site_list[0]
            site_id = str(site_dict["id"])
            return site_id
        elif response["message"] == "token verify error.":
            print ("Authentication token not valid. Requesting new token...")
            self.cookie = self.authentication_cookie()
            return False 
        else:
            print ("No valid return from API")
            return False

    def update(self):
        sid = self.get_sid()
        if sid == False:
            return False
        data = { "sid": sid } 
        response = json.loads(requests.post("https://neapi.hoymiles.com/pvm-data/api/0/station/data/count_station_real_data", headers=self.authorizationheader, json=data).text)
        if response["message"] == "success":
            self.today = str(response["data"]["today_eq"])
            self.this_month = str(response["data"]["month_eq"])
            self.this_year = str(response["data"]["year_eq"])
            self.lifetime_energy = str(response["data"]["total_eq"])
            self.current_power = str(response["data"]["real_power"])
            self.last_update = str(response["data"]["last_data_time"])
        elif response["message"] == "token verify error.":
            print ("Authentication token not valid. Requesting new token...")
            self.cookie = self.authentication_cookie()
            return False 
        else:
            print ("No valid return from API")
            return False
            
def connect_mqtt(broker, port, mqtt_username, mqtt_password):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect to mqtt, return code %d\n", rc)
            return False

    client_id = f'hoymiles-mqtt-{random.randint(0, 1000)}'
    client = mqtt_client.Client(client_id)
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client, topic, message): 
    result = client.publish(topic, message, retain=True)
    status = result[0]
    if status == 0:
        print(f"Sent `{message}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

client = connect_mqtt(MQTT_HOST_ADDRESS, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD)
client.loop_start()

hoymiles = Energy(USERNAME,USERPASSWORD)

lastUpdate = ""
energytoday = 0

while 1<2:

    current_time = datetime.now().strftime("%D %H:%M:%S")
    
    #if lastUpdate != hoymiles.last_update or energytoday != hoymiles.today:
    if energytoday != hoymiles.today:
        print ("Update at: ", current_time)
        publish(client, "hoymiles/energy_today", hoymiles.today)
        publish(client, "hoymiles/energy_this_month", hoymiles.this_month)
        publish(client, "hoymiles/energy_this_year", hoymiles.this_year)
        publish(client, "hoymiles/energy_lifetime_energy", hoymiles.lifetime_energy)
        publish(client, "hoymiles/current_power", hoymiles.current_power)
        publish(client, "hoymiles/last_update", hoymiles.last_update)
        
        lastUpdate = hoymiles.last_update
        energytoday = hoymiles.today
    else:
        print ("No new information at: ", current_time)
    

    #thisUpdateTime = datetime.now()
    #followingUpdateTime = datetime.now() + timedelta(seconds=API_FREQUENCY_CHECK)
    
    #if thisUpdateTime.day != followingUpdateTime.day:
    #    print ("Following update will be after midnight. Setting day-total to 0.")
    #    publish(client, "hoymiles/energy_today", "0")
        
    time.sleep(API_FREQUENCY_CHECK)

    result = hoymiles.update()

    if result == False:
        print ("Error happened. Data not updated!")
