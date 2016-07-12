try:
    #import urllib2 
    from urllib2 import urlopen    
    import urllib
except ImportError:
    from urllib.request import urlopen
import json

URL = "https://www.googleapis.com/youtube/v3/videoCategories"

IDS = {
    "Film & Animation": 1,
    "Autos & Vehicles": 2,
    "Music": 10,
    "Pets & Animals": 15,
    "Sports": 17,
    "Short Movies": 18,
    "Travel & Events": 19,
    "Gaming": 20,
    "Videoblogging": 21,
    "People & Blogs": 22,
    "Comedy": 34,
    "Entertainment": 24,
    "News & Politics": 25,
    "Howto & Style": 26,
    "Education": 27,
    "Science & Technology": 28,
    "Nonprofits & Activism": 29,
    "Movies": 30,
    "Anime/Animation": 31,
    "Action/Adventure": 32,
    "Classics": 33,
    "Documentary": 35,
    "Drama": 36,
    "Family": 37,
    "Foreign": 38,
    "Horror": 39,
    "Sci-Fi/Fantasy": 40,
    "Thriller": 41,
    "Shorts": 42,
    "Shows": 43,
    "Trailers": 44,
}

def get(region_code="us", api_key=None):
    params = dict(part="snippet", regionCode=region_code, key=api_key)  
    full_url = URL + "?" + urllib.urlencode(params)
    response = urlopen(full_url)
    categories_info = json.loads(response.read())
    items = categories_info["items"]
    return dict((item["snippet"]["title"], item["id"]) for item in items)
