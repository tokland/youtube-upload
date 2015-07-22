from lib import debug

def add_to_playlist(youtube, video_id, options):
    # find playlist with given name
    existing_playlist_id = None
    playlists = youtube.playlists()
    request = playlists.list(mine=True, part='id,snippet')
    while request is not None:
        results = request.execute()
        for item in results['items']:
            if item.get('snippet', {}).get('title') == options.playlist:
                existing_playlist_id = item.get('id')

        # stop paginating playlists on first matching playlist title
        if existing_playlist_id is None:
            request = playlists.list_next(request, results)
        else:
            break

    # create playlist, if necessary
    if existing_playlist_id is None:
        playlists_insert_response = youtube.playlists().insert(part="snippet,status", body={
            "snippet": {
                "title": options.playlist
            },
            "status": {
                "privacyStatus": options.privacy
            }
        }).execute()
        existing_playlist_id = playlists_insert_response.get('id', None)

    # something has gone wrong
    if existing_playlist_id is None:
        debug('Error creating playlist')
    else:
        # add video to playlist
        youtube.playlistItems().insert(part='snippet', body={
            "snippet": {
                "playlistId": existing_playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }).execute()
        debug("Added video to playlist '{0}'".format(options.playlist))