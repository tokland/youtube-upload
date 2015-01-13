Introduction
============

_Youtube-upload_ is a command-line script that uploads videos to Youtube (it should work on any platform -GNU/Linux, BSD, OS X, Windows, ...- that runs Python).

Dependencies
============

  * [Python 2.6 or 2.7](http://www.python.org). Python 3.0 is NOT supported.
  * [Python Google API](https://github.com/google/google-api-python-client)

Install
=======

```
$ wget https://github.com/tokland/youtube-upload/archive/master.zip
$ unzip master.zip
$ cd youtube-upload-master
$ sudo python setup.py install
```

  * If you don't want (or you can't) install software on the computer, run it directly from sources:

```
$ cd youtube-upload-master
$ PYTHONPATH=. python youtube_upload/youtube_upload.py ...
```

Examples
========

* Upload a video:

```
$ youtube-upload --title="A.S. Mutter" --description="A.S. Mutter plays Beethoven" \
                 --category=Music --tags="mutter, beethoven" anne_sophie_mutter.flv
pxzZ-fYjeYs
```

* Upload a video with your own ```client_secrets.json```:

```
$ youtube-upload --title="A.S. Mutter" --description="A.S. Mutter plays Beethoven" \
                 --category=Music --tags="mutter, beethoven" 
                 --client-secrets=my_client_secrets.json anne_sophie_mutter.flv
pxzZ-fYjeYs
```

* Split a video with _ffmpeg_

Youtube currently limits videos to <2Gb and <15' for almost all users. You can use the example script to split it before uploading:

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
$ export https_proxy=http://user:password@host:port
$ youtube-upload ....
```

Caveats
=======

* The package includes a default ```client_secrets.json``` file, but if you plan to make a heavy use of the script, please [create and use your own authentication file](https://developers.google.com/youtube/v3/getting-started).

* If a video does not comply with Youtube size limitations you must split it (using ffmpeg/avconvm, for example). 

More
====

* License: [GNU/GPLv3](http://www.gnu.org/licenses/gpl.html). 

* Feedback: [Open a issue](https://github.com/tokland/youtube-upload/issues).

<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
  <input type="hidden" name="cmd" value="_donations">
  <input type="hidden" name="business" value="pyarnau@gmail.com">
  <input type="hidden" name="lc" value="US">
  <input type="hidden" name="item_name" value="youtube-upload">
  <input type="hidden" name="no_note" value="0">
  <input type="hidden" name="currency_code" value="EUR">
  <input type="hidden" name="bn" value="PP-DonationsBF:btn_donateCC_LG.gif:NonHostedGuest">
  <input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
  <img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
</form>
