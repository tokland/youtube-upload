from .lib import debug


def get_playlist(youtube, title):
    """Return users's playlist by title (None if not found)"""
    playlists = youtube.playlists()
    request = playlists.list(mine=True, part='id,snippet')
    while request:
        results = request.execute()
        for item in results['items']:
            if item.get('snippet', {}).get('title') == title:
                return item.get('id')
        request = playlists.list_next(request, results)

def create_playlist(youtube, title, privacy):
    """Create a playlist by title"""
    response = youtube.playlists().insert(part="snippet,status", body={
        "snippet": {
            "title": title,
        },
        "status": {
            "privacyStatus": privacy,
        }
    }).execute()
    return response.get('id', None)

def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add video to playlist (by identifier)."""
    return youtube.playlistItems().insert(part='snippet', body={
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }).execute()
    return playlist_id
    
def add_to_playlist(youtube, video_id, title, privacy="public"):
    """Add video to playlist (by title)."""
    playlist_id = get_playlist(youtube, title) or \
        create_playlist(youtube, title, privacy)
    if playlist_id:
        return add_video_to_playlist(youtube, playlist_id, video_id)
