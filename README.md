**THIS PROJECT NEEDS A MAINTAINER**. If someone is willing to take over the project, let me know (pyarnau AT gmail.com).

Introduction
============

Command-line script to upload videos to Youtube using theYoutube [APIv3](https://developers.google.com/youtube/v3/). It should work on any platform (GNU/Linux, BSD, OS X, Windows, ...) that runs Python.

Dependencies
============

  * [Python 2.6/2.7/3.x](http://www.python.org).
  * Packages: [google-api-python-client](https://developers.google.com/api-client-library/python), [progressbar2](https://pypi.python.org/pypi/progressbar2) (optional).

Check if your operating system provides those packages (check also those [deb/rpm/mac files](https://github.com/qiuwei/youtube-upload/releases)), otherwise install them with `pip`:

```
$ sudo pip install --upgrade google-api-python-client oauth2client progressbar2
```

Install
=======

```
$ wget https://github.com/tokland/youtube-upload/archive/master.zip
$ unzip master.zip
$ cd youtube-upload-master
$ sudo python setup.py install
```

Or run directly from sources:

```
$ cd youtube-upload-master
$ PYTHONPATH=. python bin/youtube-upload ...
```

Setup
=====

You'll see that there is no email/password options. Instead, the Youtube API uses [OAuth 2.0](https://developers.google.com/accounts/docs/OAuth2) to authenticate the upload. The first time you try to upload a video, you will be asked to follow a URL in your browser to get an authentication token. If you have multiple channels for the logged in user, you will also be asked to pick which one you want to upload the videos to. You can use multiple credentials, just use the option ```--credentials-file```. Also, check the [token expiration](https://developers.google.com/youtube/v3/) policies.

The package used to include a default ```client_secrets.json``` file. It does not work anymore, Google has revoked it. So you now must [create and use your own OAuth 2.0 file](https://developers.google.com/youtube/registering_an_application), it's a free service. Steps:

* Go to the Google [console](https://console.developers.google.com/).
* _Create project_.
* Side menu: _APIs & auth_ -> _APIs_
* Top menu: _Enabled API(s)_: Enable all Youtube APIs.
* Side menu: _APIs & auth_ -> _Credentials_.
* _Create a Client ID_: Add credentials -> OAuth 2.0 Client ID -> Other -> Name: youtube-upload -> Create -> OK
* _Download JSON_: Under the section "OAuth 2.0 client IDs". Save the file to your local system. 
* Use this JSON as your credentials file: `--client-secrets=CLIENT_SECRETS` or copy it to `~/client_secrets.json`.

*Note: ```client_secrets.json``` is a file you can download from the developer console, the credentials file is something auto generated after the first time the script is run and the google account sign in is followed, the file is stored at ```~/.youtube-upload-credentials.json```.*

Examples
========

* Upload a video (a valid `~/.client_secrets.json` should exist, check the Setup section):

```
$ youtube-upload --title="A.S. Mutter" anne_sophie_mutter.flv
pxzZ-fYjeYs
```

* Upload a video with extra metadata, with your own client secrets and credentials file, and to a playlist (if not found, it will be created):

```
$ youtube-upload \
  --title="A.S. Mutter" " \
  --description="A.S. Mutter plays Beethoven" \
  --category="Music" \
  --tags="mutter, beethoven" \
  --recording-date="2011-03-10T15:32:17.0Z" \
  --default-language="en" \
  --default-audio-language="en" \
  --client-secrets="my_client_secrets.json" \
  --credentials-file="my_credentials.json" \
  --playlist="My favorite music" \
  --embeddable=True|False \
  anne_sophie_mutter.flv
tx2Zb-145Yz
```
*Other extra medata available :* 
 ```
 --privacy (public | unlisted | private)  
 --publish-at (YYYY-MM-DDThh:mm:ss.sZ)  
 --location (latitude=VAL,longitude=VAL[,altitude=VAL])  
 --thumbnail (string)  
 ```

* Upload a video using a browser GUI to authenticate:

```
$ youtube-upload --title="A.S. Mutter" --auth-browser anne_sophie_mutter.flv
```

* Split a video with _ffmpeg_

If your video is too big or too long for Youtube limits, split it before uploading:

```
$ bash examples/split_video_for_youtube.sh video.avi
video.part1.avi
video.part2.avi
video.part3.avi
```
* Use a HTTP proxy

Set environment variables *http_proxy* and *https_proxy*:

```
$ export http_proxy=http://user:password@host:port
$ export https_proxy=$http_proxy
$ youtube-upload ....
```

Get available categories
========================

* Go to the [API Explorer](https://developers.google.com/apis-explorer)
- Search "youtube categories" -> *youtube.videoCategories.list*
- This bring you to [youtube.videoCategories.list service](https://developers.google.com/apis-explorer/#search/youtube%20categories/m/youtube/v3/youtube.videoCategories.list)
- part: `id,snippet`
- regionCode: `es` (2 letter code of your country)
- _Authorize and execute_

And see the JSON response below. Note that categories with the attribute `assignable` equal to `false` cannot be used.

Using [shoogle](https://github.com/tokland/shoogle):

```
$ shoogle execute --client-secret-file client_secret.json \
                  youtube:v3.videoCategories.list <(echo '{"part": "id,snippet", "regionCode": "es"}')  | 
    jq ".items[] | select(.snippet.assignable) | {id: .id, title: .snippet.title}"
```

Notes for developers
====================

* Main logic of the upload: [main.py](youtube_upload/main.py) (function ```upload_video```).
* Check the [Youtube Data API](https://developers.google.com/youtube/v3/docs/).
* Some Youtube API [examples](https://github.com/youtube/api-samples/tree/master/python) provided by Google.

Alternatives
============

* [shoogle](https://github.com/tokland/shoogle) can send requests to any Google API service, so it can be used not only to upload videos, but also to perform any operation regarding the Youtube API.

* [youtubeuploader](https://github.com/porjo/youtubeuploader) uploads videos to Youtube from local disk or from the web. It also provides rate-limited uploads.

More
====

* License: [GNU/GPLv3](http://www.gnu.org/licenses/gpl.html).

Feedback
========

* [Donations](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=pyarnau%40gmail%2ecom&lc=US&item_name=youtube%2dupload&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHostedGuest).
* If you find a bug, [open an issue](https://github.com/tokland/youtube-upload/issues).
* If you want a new feature to be added, you'll have to send a pull request (or find a programmer to do it for you), currently I am not adding new features.
