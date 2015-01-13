Introduction
============

_Youtube-upload_ is a command-line script that uploads videos to Youtube. 

If a video does not comply with Youtube size limitations you must split it before using ffmpeg/avconv or any other tool. _Youtube-upload_ should work on any platform (GNU/Linux, BSD, OS X, Windows, ...) that runs Python.

Dependencies
============

  * [Python 2.6 or 2.7](http://www.python.org)
  * [Python Google API](https://github.com/google/google-api-python-client)

Download & Install

```
$ wget https://github.com/tokland/youtube-upload/archive/master.zip
$ unzip master.zip
$ cd youtube-upload-master
$ sudo python setup.py install
```

  * If you don't want (or you can't) install software on the computer, run it directly from sources:

```
$ cd youtube-upload-VERSION
$ PYTHONPATH=. python youtube_upload/youtube_upload.py ...
```

Usage examples
==============

* Upload a video:

```
$ youtube-upload --title="A.S. Mutter" --description="A.S. Mutter plays Beethoven" \
                 --category=Music --keywords="mutter, beethoven" anne_sophie_mutter.flv
pxzZ-fYjeYs
```

* Upload a video with your own ```client_secrets.json```:

The package includes a default file but if you plan to use a heavy usage of the script, please [create and use your own authentication file](https://developers.google.com/youtube/v3/getting-started). 

```
$ youtube-upload --title="A.S. Mutter" --description="A.S. Mutter plays Beethoven" \
                 --category=Music --keywords="mutter, beethoven" 
                 --client-secrets=my_client_secrets.json anne_sophie_mutter.flv
pxzZ-fYjeYs
```

* Split a video with _ffmpeg_

Youtube currently limits videos to <2Gb and <15' for almost all users. You can use the Bash example script to split it before uploading:

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

More
====

* License: GNU/GPL v3 

* [Open an issue](https://github.com/tokland/youtube-upload/issues)

*[Donate to the develper with PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=pyarnau%40gmail%2ecom&lc=US&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHostedGuest)
