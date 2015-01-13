from apiclient.http import MediaFileUpload

def upload(youtube_resource, video_path, body, chunksize=1024*1024, progress_callback=None):
    body_keys = ",".join(body.keys())
    media = MediaFileUpload(video_path, chunksize=chunksize, resumable=True)
    videos = youtube_resource.videos()
    request = videos.insert(part=body_keys, body=body, media_body=media)
    
    while 1:
        status, response = request.next_chunk()
        if response:
            if "id" in response:
                return response['id']
            else:
                raise KeyError("Response has no 'id' field")
        elif status and progress_callback:
            progress_callback(status.total_size, status.resumable_progress)
