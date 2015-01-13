Introduction
============

_Youtube-upload_ is a command-line script that uploads videos to Youtube. 

If a video does not comply with Youtube size limitations you must split it before using ffmpeg/avconv or any other tool. _Youtube-upload_ should work on any platform (GNU/Linux, BSD, OS X, Windows, ...) that runs Python.

Dependencies
============

  * [http://www.python.org python 2.6 or 2.7]
  * [https://code.google.com/p/google-api-python-client/ python2-google-api-python-client] (>= 1.3.1)

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

Feedback
========

https://github.com/tokland/youtube-upload/issues
