from openai import OpenAI
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, render_template, request
import os

# Load API keys from .env
load_dotenv()
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        vibe = request.form.get("taste")

        # Prompt GPT for playlist
        prompt = f"""
        Create a 1.5-hour Spotify-style playlist for this vibe: "{vibe}"
        Return:
        1. A one-sentence fun description of the vibe and the top song.
        2. A top song recommendation in 'Artist - Song Title' format.
        3. A list of 15 real songs (also in 'Artist - Song Title' format).
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=400
        )

        result = response.choices[0].message.content
        lines = result.split("\n")

        # ✅ Initialize vars
        description = ""
        top_song_title = None
        playlist = []

        # ✅ Parse GPT response
        for line in lines:
            if "description" in line.lower() or "vibe" in line.lower():
                description = line.strip()
            elif "top song" in line.lower():
                top_song_title = line.split(":", 1)[-1].strip()
            elif "-" in line and not line.lower().startswith("top"):
                playlist.append(line.strip("•- ").strip())

        # ✅ Fetch Spotify metadata for playlist
        song_data = []
        for song in playlist:
            try:
                results = sp.search(q=song, type='track', limit=1)
                track = results['tracks']['items'][0]
                song_data.append({
                    "title": track['name'],
                    "artist": track['artists'][0]['name'],
                    "image": track['album']['images'][0]['url'],
                    "url": track['external_urls']['spotify'],
                    "preview": track['preview_url']
                })
            except:
                song_data.append({
                    "title": song,
                    "artist": "Unknown",
                    "image": None,
                    "url": "#",
                    "preview": None
                })

        # ✅ Fetch top song info
        if top_song_title:
            try:
                top_results = sp.search(q=top_song_title, type='track', limit=1)
                top_track = top_results['tracks']['items'][0]
                top_song_data = {
                    "title": top_track['name'],
                    "artist": top_track['artists'][0]['name'],
                    "image": top_track['album']['images'][0]['url'],
                    "url": top_track['external_urls']['spotify'],
                    "preview": top_track['preview_url']
                }
            except:
                top_song_data = {
                    "title": top_song_title,
                    "artist": "Unknown",
                    "image": None,
                    "url": "#",
                    "preview": None
                }
        else:
            top_song_data = {
                "title": "Unavailable",
                "artist": "Unknown",
                "image": None,
                "url": "#",
                "preview": None
            }

        # ✅ Render results
        return render_template(
            "results.html",
            user_prompt=vibe,
            description=description,
            top_song=top_song_data,
            songs=song_data
        )

    # GET fallback
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
