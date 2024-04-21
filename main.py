import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from flask import Flask
import json

CLIENT_TOKEN = os.environ["CLIENT_TOKEN"]

sp = spotipy.Spotify(auth=CLIENT_TOKEN)

playlists = sp.current_user_playlists()['items']
real_talk = None

for i, playlist in enumerate(playlists):
    if 'real talk' in playlist['name'].lower():
        real_talk = playlist

real_talk_tracks = sp.playlist_tracks(real_talk['id'])['items']
real_talk_tracks = {track['track']['id']: track['track']['name']
                    for track in real_talk_tracks}


def current_track_is_real_talk():
    current_id = sp.currently_playing()

    if current_id != None:
        current_id = current_id['item']['id']

        return {'id': current_id, 'name': real_talk_tracks[current_id]['name'], 'img': real_talk_tracks[current_id]['album']['images'][2]['url']} if current_id in real_talk_tracks.keys() else {'id': None, 'name': None, 'img': None}

    return {'id': None, 'name': None, 'img': None}


app = Flask(__name__)


@app.route('/')
def hello_world():
    return json.dumps(current_track_is_real_talk())

