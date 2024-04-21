from flask import Flask, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import os
import json
import base64
import requests
import random

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SCOPE = "user-library-read user-read-currently-playing"
REFRESH_TOKEN = os.environ['REFRESH_TOKEN']


def refresh_access_token():
    auth_client = CLIENT_ID + ":" + CLIENT_SECRET
    auth_encode = 'Basic ' + \
        base64.b64encode(auth_client.encode()).decode()

    headers = {
        'Authorization': auth_encode,
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }

    response = requests.post('https://accounts.spotify.com/api/token',
                             data=data, headers=headers)  # sends request off to spotify

    if (response.status_code == 200):  # checks if request was valid
        print("The request to went through we got a status 200; Spotify token refreshed")
        response_json = response.json()
        new_expire = response_json['expires_in']
        print("the time left on new token is: " +
              str(new_expire / 60) + "min")  # says how long
        return response_json["access_token"]
    else:
        print("ERROR! The response we got was: " + str(response))


access_token = refresh_access_token()

sp = spotipy.Spotify(
    auth=access_token)

playlists = sp.current_user_playlists()['items']
real_talk = None

for i, playlist in enumerate(playlists):
    if 'real talk' in playlist['name'].lower():
        real_talk = playlist

real_talk_tracks = sp.playlist_tracks(real_talk['id'])['items']
real_talk_tracks = {track['track']['id']: track['track']
                    for track in real_talk_tracks}


def current_track_is_real_talk():
    current = None
    try:
        current = sp.currently_playing()
    except:
        access_token = refresh_access_token()
        current = sp.currently_playing()

    if current != None:
        name = current['item']['name']
        img = current['item']['album']['images'][2]['url']
        current_id = current['item']['id']

        return {'id': current_id, 'name': name, 'img': img, 'real_talk': current_id in real_talk_tracks.keys()}

    NOTHING_IS_PLAYING = ["Spotify", "Nothing's playing...",
                          "Huh?", "Spotify.com", "Apple music 🤮"]

    return {'id': None, 'name': random.choice(NOTHING_IS_PLAYING), 'img': None, 'real_talk': False}


app = Flask(__name__)


@app.route('/')
def hello_world():
    return json.dumps(current_track_is_real_talk())


@app.route('/image')
def get_image():
    def get_image_url():
        track = current_track_is_real_talk()
        if track['id']:
            return track['img']

        return "https://m.media-amazon.com/images/I/51rttY7a+9L.png"

    url = get_image_url()

    return redirect(url)
