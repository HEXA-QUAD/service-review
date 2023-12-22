import requests
from flask import Flask, jsonify, request, url_for
import json

text = None
# api_url = 'https://api.api-ninjas.com/v1/profanityfilter?text={}'.format(text)
api_url = 'https://api.api-ninjas.com/v1/profanityfilter?text='+'{}'.format(text)
response = requests.get(api_url, headers={'X-Api-Key': 'M0eB3+yE0Y1SeYEcPge8pw==RCoIJ0GIrXiOguwn'})
if response.status_code == requests.codes.ok:
    print(response.text)
    data = json.loads(response.text)
    print(data)
else:
    print("Error:", response.status_code, response.text)