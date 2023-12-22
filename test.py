import requests

text = ('damn it! the worst course in the world!')
api_url = 'https://api.api-ninjas.com/v1/profanityfilter?text={}'.format(text)
response = requests.get(api_url, headers={'X-Api-Key': 'M0eB3+yE0Y1SeYEcPge8pw==RCoIJ0GIrXiOguwn'})
if response.status_code == requests.codes.ok:
    print(response.text)
else:
    print("Error:", response.status_code, response.text)