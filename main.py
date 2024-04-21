# import libraries
from flask import Flask, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import os
import json
import base64
import requests
import random

# load environment variables
# should be stored in render
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ['REFRESH_TOKEN']

# constants
SCOPE = "user-library-read user-read-currently-playing"

# define access token reload
# access tokens last for 60 minutes
# you can obtain an access token by requesting one from the spotify api using a refresh token
# the method to obtain a refresh token is detailed here:
# https://dev.to/sabareh/how-to-get-the-spotify-refresh-token-176
# the second method shown worked best for me
# (if you're on windows make sure to use command prompt to enter the curl command)
def refresh_access_token():
    # convert to a request url
    auth_client = CLIENT_ID + ":" + CLIENT_SECRET
    auth_encode = 'Basic ' + \
        base64.b64encode(auth_client.encode()).decode()

    headers = {
        'Authorization': auth_encode,
    }

    # designate grant type and specify refresh token
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN # environemnt secret
    }

    # send request off to spotify
    response = requests.post('https://accounts.spotify.com/api/token',
                             data=data, headers=headers)
      # check if request was valid
    if (response.status_code == 200):
        print("The request to went through we got a status 200; Spotify token refreshed")
        response_json = response.json()
        new_expire = response_json['expires_in']
        print("the time left on new token is: " +
              str(new_expire / 60) + "min")  # says how long
        return response_json["access_token"]
    else:
        # rip
        print("ERROR! The response we got was: " + str(response))

# obtain fresh access token at start
access_token = refresh_access_token()

# create spotipy object
sp = spotipy.Spotify(auth=access_token)

# locate playlists
playlists = sp.current_user_playlists()['items']

# search through and find real talk playlist
real_talk = None

for i, playlist in enumerate(playlists):
    if 'real talk' in playlist['name'].lower():
        real_talk = playlist

# filter the tracks to preserve meaningful data
real_talk_tracks = sp.playlist_tracks(real_talk['id'])['items']
real_talk_tracks = {track['track']['id']: track['track']
                    for track in real_talk_tracks}

def current_track_is_real_talk():
    # make sure a track is playing
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

        # return in a dict format with only relevant data
        return {'id': current_id, 'name': name, 'img': img, 'real_talk': current_id in real_talk_tracks.keys()}

    # no track is playing :(
    NOTHING_IS_PLAYING = ["Spotify", "Nothing's playing...",
                          "Huh?", "Spotify.com", "Apple music 🤮"]

    return {'id': None, 'name': random.choice(NOTHING_IS_PLAYING), 'img': None, 'real_talk': False}

# flask stuff (blegh)
app = Flask(__name__)


@app.route('/')
def hello_world():
    # return a json str for widgy to parse
    return json.dumps(current_track_is_real_talk())


@app.route('/image')
def get_image():
    # redirect widgy to the image data
    def get_image_url():
        track = current_track_is_real_talk()
        if track['id']:
            return track['img']

        # no song is being played so show spotify logo
        return "https://m.media-amazon.com/images/I/51rttY7a+9L.png"

    url = get_image_url()

    return redirect(url)
