import string    
import random 
import requests
import subprocess
from sys import path
import os

# Check API connection wiith https://git.mclarkdev.com/BarcodeAPI.org/server
try:
    api_response = requests.get('https://barcodeapi.org/api/128/abc123')
    api_response.raise_for_status()
except requests.exceptions.RequestException as err:
    print ("OOps: Something Else",err)
except requests.exceptions.HTTPError as errh:
    print ("Http Error:",errh)
except requests.exceptions.ConnectionError as errc:
    print ("Error Connecting:",errc)
except requests.exceptions.Timeout as errt:
    print ("Timeout Error:",errt)   

S = 5  # number of characters in the string.  
i = 0 #number of barcode user what

barcode_folder = path[0] + '/known_barcode'
if not os.path.exists(barcode_folder):
   os.makedirs(barcode_folder)

while i < 5:
    #change ASIN to what you intended to use
    #barcode = 'hcX'.join(random.choices(string.ascii_uppercase + string.digits, k = S))
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))  
    barcode = f"hcX{random_part}"
    print("The randomly generated string is : " + str(barcode)) # print the random data
    
    url = 'https://barcodeapi.org/api/128/' + str(barcode)
    filename = barcode_folder + '/' + '_' + str(barcode) + '.png'
    subprocess.run(["curl", url, "--output", filename])
    i +=1



