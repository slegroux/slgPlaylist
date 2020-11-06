#!/usr/bin/env python
# 11/05/20 sylvain // telegram: @slegroux

import requests
from bs4 import BeautifulSoup
import spacy
import musicbrainzngs
import pycountry
import spotipy
import os
import argparse
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy.util as util

ID = os.environ.get('SPOTIFY_ID')
SECRET = os.environ.get('SPOTIFY_SECRET')
REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')

# sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=ID, client_secret=SECRET))
scope = 'playlist-modify-public'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=ID,
                                               client_secret=SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))

musicbrainzngs.set_useragent("sic-censored", "0.1", "http://example.com")
nlp = spacy.load("en_core_web_sm")


def get_args():
    parser = argparse.ArgumentParser(description='test freemuse=>musicbrainz=>spotify')
    # TODO: just pass country and map region
    parser.add_argument('-r', '--region', required=True, default='europe',
                        help='europe/africa/asia/north-south-america/middle-east-north-africa')
    parser.add_argument('-c', '--country', required=True, default='spain',
                        help='country')
    return parser.parse_args()


def get_artists_from_freemuse(region, country):
    artists = set()
    # TODO: parse through all pages not just first one
    url = "https://freemuse.org/regions" + "/" + region + "/" + country
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    items = soup.find_all(class_="item-list")
    for item in items:
        entry = item.find(class_="entry")
        article = entry.find('p').getText()
        doc = nlp(article)
        # keep only persons 
        # TODO: sometimes actually ORG is relevant too
        entities = [x.text for x in doc.ents if (x.label_ == 'PERSON')]
        if entities:
            for entity in entities:
                # cross check person with musicbrainz so we make sure the artist exists in the specified country
                # TODO: not very robust. find some way to double check

                artist_in_musicbrainz = musicbrainzngs.search_artists(artist=entity, country=pycountry.countries.get(name=country).alpha_2)['artist-list'][0]['name']
                artists.add(artist_in_musicbrainz)
    return(artists)


def top_tracks_on_spotify(artist):
    uri = sp.search(artist)['tracks']['items'][0]['artists'][0]['uri']
    response = sp.artist_top_tracks(uri)
    return(response['tracks'])


def create_spotify_playlist(tids, name='sic-censored'):
    user_id = sp.me()['id']
    pl = sp.user_playlist_create(user_id, name)
    sp.playlist_add_items(pl['id'], tids)
    

if __name__ == "__main__":

    args = get_args()
    region = args.region
    country = args.country
    artists = get_artists_from_freemuse(region, country)

    tids = []
    for artist in artists:
        tops = top_tracks_on_spotify(artist)
        for track in tops:
            print(artist, track['name'])
            tids.append(track['id'])

    create_spotify_playlist(tids,'sic-censored' +'_' + region + '_' + country)

