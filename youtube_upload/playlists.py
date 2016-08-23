import locale

from .lib import debug

def get_playlist(youtube, title):
    """Return users's playlist ID by title (None if not found)"""
    playlists = youtube.playlists()
    request = playlists.list(mine=True, part="id,snippet")
    current_encoding = locale.getpreferredencoding()
    
    while request:
        results = request.execute()
        for item in results["items"]:
            t = item.get("snippet", {}).get("title")
            existing_playlist_title = (t.encode(current_encoding) if hasattr(t, 'decode') else t)
            if existing_playlist_title == title:
                return item.get("id")
        request = playlists.list_next(request, results)

def create_playlist(youtube, title, privacy):
    """Create a playlist by title and return its ID"""
    debug("Creating playlist: {0}".format(title))
    response = youtube.playlists().insert(part="snippet,status", body={
        "snippet": {
            "title": title,
        },
        "status": {
            "privacyStatus": privacy,
        }
    }).execute()
    return response.get("id")

def add_video_to_existing_playlist(youtube, playlist_id, video_id):
    """Add video to playlist (by identifier) and return the playlist ID."""
    debug("Adding video to playlist: {0}".format(playlist_id))
    return youtube.playlistItems().insert(part="snippet", body={
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            }
        }
    }).execute()
    
def add_video_to_playlist(youtube, video_id, title, privacy="public"):
    """Add video to playlist (by title) and return the full response."""
    playlist_id = get_playlist(youtube, title) or \
        create_playlist(youtube, title, privacy)
    if playlist_id:
        return add_video_to_existing_playlist(youtube, playlist_id, video_id)
    else:
        debug("Error adding video to playlist")
