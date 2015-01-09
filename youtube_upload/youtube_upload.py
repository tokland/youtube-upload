#!/usr/bin/python2
#
# Youtube-upload is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Youtube-upload is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Youtube-upload. If not, see <http://www.gnu.org/licenses/>.
#
# Author: Arnau Sanchez <tokland@gmail.com>
# Websites: http://code.google.com/p/youtube-upload
#           http://code.google.com/p/tokland
"""
Upload a video to Youtube from the command-line.

    $ youtube-upload --email=myemail@gmail.com \
                     --password=mypassword \
                     --title="A.S. Mutter playing" \
                     --description="Anne Sophie Mutter plays Beethoven" \
                     --category=Music \
                     --keywords="mutter, beethoven" \
                     anne_sophie_mutter.flv
    www.youtube.com/watch?v=pxzZ-fYjeYs
"""

import os
import re
import sys
import time
import string
import locale
import urllib
import socket
import getpass
import StringIO
import optparse
import itertools
# python >= 2.6
from xml.etree import ElementTree

# python-gdata (>= 1.2.4)
import gdata.media
import gdata.service
import gdata.geo
import gdata.youtube
import gdata.youtube.service
from gdata.media import YOUTUBE_NAMESPACE
from atom import ExtensionElement

# http://pycurl.sourceforge.net/
try:
    import pycurl
except ImportError:
    pycurl = None

# http://code.google.com/p/python-progressbar (>= 2.3)
try:
    import progressbar
except ImportError:
    progressbar = None

class InvalidCategory(Exception): pass
class VideoArgumentMissing(Exception): pass
class OptionsMissing(Exception): pass
class BadAuthentication(Exception): pass
class CaptchaRequired(Exception): pass
class ParseError(Exception): pass
class VideoNotFound(Exception): pass
class UnsuccessfulHTTPResponseCode(Exception): pass

VERSION = "0.7.4"
DEVELOPER_KEY = "AI39si7iJ5TSVP3U_j4g3GGNZeI6uJl6oPLMxiyMst24zo1FEgnLzcG4i" + \
  "SE0t2pLvi-O03cW918xz9JFaf_Hn-XwRTTK7i1Img"

EXIT_CODES = {
    # Non-retryable
    BadAuthentication: 1,
    VideoArgumentMissing: 2,
    OptionsMissing: 2,
    InvalidCategory: 3,
    CaptchaRequired: 4, # retry with options --captcha-token and --captcha-response
    ParseError: 5,
    VideoNotFound: 6,
    # Retryable
    UnsuccessfulHTTPResponseCode: 100,
}

def to_utf8(s):
    """Re-encode string from the default system encoding to UTF-8."""
    current = locale.getpreferredencoding()
    return (s.decode(current).encode("UTF-8") if s and current != "UTF-8" else s)

def debug(obj, fd=sys.stderr):
    """Write obj to standard error."""
    string = str(obj.encode(get_encoding(fd), "backslashreplace")
        if isinstance(obj, unicode) else obj)
    fd.write(string + "\n")

def catch_exceptions(exit_codes, fun, *args, **kwargs):
    """
    Catch exceptions on 'fun(*args, **kwargs)' and return the exit code specified 
    in the 'exit_codes' dictionary. Returns 0 if no exception is raised.
    """
    try:
        fun(*args, **kwargs)
        return 0
    except tuple(exit_codes.keys()) as exc:
        debug("[%s] %s" % (exc.__class__.__name__, exc))
        return exit_codes[exc.__class__]

def get_encoding(fd):
    """Guess terminal encoding."""
    return fd.encoding or locale.getpreferredencoding()

def compact(it):
    """Filter false (in the truth sense) elements in iterator."""
    return filter(bool, it)

def tosize(seq, size):
    """Return a list of fixed length from sequence (which may be shorter or longer)."""
    return (seq[:size] if len(seq) >= size else (seq + [None] * (size-len(seq))))

def first(it):
    """Return first element in iterable."""
    return it.next()

def post(url, files_params, extra_params, show_progressbar=True):
    """Post files to a given URL."""
    def progress(bar, maxval, download_t, download_d, upload_t, upload_d):
        bar.update(min(maxval, upload_d))
    c = pycurl.Curl()
    file_params2 = [(key, (pycurl.FORM_FILE, path)) for (key, path) in files_params.items()]
    items = extra_params.items() + file_params2
    c.setopt(c.URL, url + "?nexturl=http://code.google.com/p/youtube-upload")
    c.setopt(c.HTTPPOST, items)
    if show_progressbar and progressbar:
        widgets = [
            progressbar.Percentage(), ' ',
            progressbar.Bar(), ' ',
            progressbar.ETA(), ' ',
            progressbar.FileTransferSpeed(),
        ]
        total_filesize = sum(os.path.getsize(path) for path in files_params.values())
        bar = progressbar.ProgressBar(widgets=widgets, maxval=total_filesize)
        bar.start()
        c.setopt(c.NOPROGRESS, 0)
        c.setopt(c.PROGRESSFUNCTION, lambda *args: progress(bar, total_filesize, *args))
    elif show_progressbar:
        debug("Install python-progressbar to see a nice progress bar")
        bar = None
    else:
        bar = None
        
    body_container = StringIO.StringIO()
    headers_container = StringIO.StringIO()
    c.setopt(c.WRITEFUNCTION, body_container.write)
    c.setopt(c.HEADERFUNCTION, headers_container.write)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.perform()
    http_code = c.getinfo(pycurl.HTTP_CODE)
    c.close()
    
    if bar:
        bar.finish()
    headers = dict([s.strip() for s in line.split(":", 1)] for line in
      headers_container.getvalue().splitlines() if ":" in line)
    return http_code, headers, body_container.getvalue()

class Youtube:
    """Interface the Youtube API."""
    CATEGORIES_SCHEME = "http://gdata.youtube.com/schemas/2007/categories.cat"

    def __init__(self, developer_key, source="tokland-youtube_upload",
            client_id="tokland-youtube_upload"):
        """Login and preload available categories."""
        service = gdata.youtube.service.YouTubeService()
        service.ssl = False # SSL is not yet supported by the API
        service.source = source
        service.developer_key = developer_key
        service.client_id = client_id
        self.service = service

    def login(self, email, password, captcha_token=None, captcha_response=None):
        """Login into youtube."""
        self.service.email = email
        self.service.password = password
        self.service.ProgrammaticLogin(captcha_token, captcha_response)

    def get_upload_form_data(self, path, *args, **kwargs):
        """Return dict with keys 'post_url' and 'token' with upload info."""
        entry = self._create_video_entry(*args, **kwargs)
        post_url, token = self.service.GetFormUploadToken(entry)
        return dict(entry=entry, post_url=post_url, token=token)

    def upload_video(self, path, *args, **kwargs):
        """Upload a video."""
        video_entry = self._create_video_entry(*args, **kwargs)
        return self.service.InsertVideoEntry(video_entry, path)

    def create_playlist(self, title, description, private=False):
        """Create a new playlist and return its uri."""
        playlist = self.service.AddPlaylist(title, description, private)
        # playlist.GetFeedLink() returns None, why?
        return first(el.get("href") for el in playlist._ToElementTree() if "feedLink" in el.tag)

    def add_video_to_playlist(self, video_id, playlist_uri, title=None, description=None):
        """Add video to playlist."""
        expected = r"http://gdata.youtube.com/feeds/api/playlists/"
        if not re.match("^" + expected, playlist_uri):
            raise ParseError("expecting playlist feed URL (%sID), but got '%s'" %
                  (expected.decode("string-escape"), playlist_uri))
        playlist_video_entry = self.service.AddPlaylistVideoEntryToPlaylist(
            playlist_uri, video_id, title, description)
        return playlist_video_entry

    def update_metadata(self, url, title, description, keywords):
        """Change metadata of a video."""
        entry = self._get_feed_from_url(url)
        if title:
            entry.media.title = gdata.media.Title(text=title)
        if description:
            entry.media.description = \
                gdata.media.Description(description_type='plain', text=description)
        if keywords:
          entry.media.keywords = gdata.media.Keywords(text=keywords)
        return self.service.UpdateVideoEntry(entry)

    def delete_video_from_playlist(self, video_id, playlist_uri):
        """Delete video from playlist."""
        expected = r"http://gdata.youtube.com/feeds/api/playlists/"
        if not re.match("^" + expected, playlist_uri):
            raise ParseError("expecting playlist feed URL (%sID), but got '%s'" %
                  (expected.decode("string-escape"), playlist_uri))
        entries = self.service.GetYouTubePlaylistVideoFeed(playlist_uri).entry
        
        for entry in entries:
            url, entry_id = get_entry_info(entry)
            if video_id == entry_id:
                playlist_video_entry_id = entry.id.text.split('/')[-1]
                self.service.DeletePlaylistVideoEntry(playlist_uri, playlist_video_entry_id)
                break
        else:
            raise VideoNotFound("Video %s not found in playlist %s" % (video_id, playlist_uri)) 

    def check_upload_status(self, video_id):
        """
        Check upload status of a video.

        Return None if video is processed, and a pair (status, message) otherwise.
        """
        return self.service.CheckUploadStatus(video_id=video_id)

    def _get_feed_from_url(self, url):
        template = 'http://gdata.youtube.com/feeds/api/users/default/uploads/%s' 
        video_id = get_video_id_from_url(url)
        return self.service.GetYouTubeVideoEntry(template % video_id)

    def _create_video_entry(self, title, description, category, keywords=None,
            location=None, private=False, unlisted=False, recorded=None, 
            nocomments=False, noratings=False):
        self.categories = self.get_categories()
        if category not in self.categories:
            valid = " ".join(self.categories.keys())
            raise InvalidCategory("Invalid category '%s' (valid: %s)" % (category, valid))
        media_group = gdata.media.Group(
            title=gdata.media.Title(text=title),
            description=gdata.media.Description(description_type='plain', text=description),
            keywords=gdata.media.Keywords(text=keywords),
            category=gdata.media.Category(
                text=category,
                label=self.categories[category],
                scheme=self.CATEGORIES_SCHEME),
            private=(gdata.media.Private() if private else None),
            player=None)
        
        if location:
            where = gdata.geo.Where()
            where.set_location(location)
        else:
            where = None
        
        extensions = []
        
        if unlisted:
            list_denied = {
                "namespace": YOUTUBE_NAMESPACE,
                "attributes": {'action': 'list', 'permission': 'denied'},
            }
            extensions.append(ExtensionElement('accessControl', **list_denied))

        if nocomments:
            comment_denied = {
                "namespace": YOUTUBE_NAMESPACE,
                "attributes": {'action': 'comment', 'permission': 'denied'},
            }
            extensions.append(ExtensionElement('accessControl', **comment_denied))

        if noratings:
            rate_denied = {
                "namespace": YOUTUBE_NAMESPACE,
                "attributes": {'action': 'rate', 'permission': 'denied'},
            }
            extensions.append(ExtensionElement('accessControl', **rate_denied))
        when = (gdata.youtube.Recorded(None, None, recorded) if recorded else None)
        return gdata.youtube.YouTubeVideoEntry(media=media_group, geo=where,
            recorded=when, extension_elements=extensions)

    @classmethod
    def get_categories(cls):
        """Return categories dictionary with pairs (term, label)."""
        def get_pair(element):
            """Return pair (term, label) for a (non-deprecated) XML element."""
            if all(not(str(x.tag).endswith("deprecated")) for x in element.getchildren()):
                return (element.get("term"), element.get("label"))
        xmldata = str(urllib.urlopen(cls.CATEGORIES_SCHEME).read())
        xml = ElementTree.XML(xmldata)
        return dict(compact(map(get_pair, xml)))


def get_video_id_from_url(url):
    """Return video ID from a Youtube URL."""
    match = re.search("v=(.*)$", url)
    if not match:
        raise ParseError("expecting a video URL (http://www.youtube.com?v=ID), but got '%s'" % url)
    return match.group(1)

def get_entry_info(entry):
    """Return pair (url, id) for video entry."""
    url = entry.GetHtmlLink().href.replace("&feature=youtube_gdata", "")
    video_id = get_video_id_from_url(url)
    return url, video_id

def parse_location(string):
    """Return tuple (long, latitude) from string with coordinates."""
    if string and string.strip():
        return map(float, string.split(",", 1))

def wait_processing(youtube_obj, video_id):
    """Wait until a video id recently uploaded has been procesed."""
    debug("waiting until video is processed")
    while 1:
        try:
          response = youtube_obj.check_upload_status(video_id)
        except socket.gaierror as msg:
          debug("non-fatal network error: %s" % msg)
          continue
        if not response:
            debug("video is processed")
            break
        status, message = response
        debug("check_upload_status: %s" % " - ".join(compact(response)))
        if status != "processing":
            break
        time.sleep(5)

def upload_video(youtube, options, video_path, total_videos, index):
    """Upload video with index (for split videos)."""
    title = to_utf8(options.title)
    description = to_utf8(options.description or "").decode("string-escape")
    namespace = dict(title=title, n=index+1, total=total_videos)
    complete_title = (string.Template(options.title_template).substitute(**namespace)
      if total_videos > 1 else title)
    args = [video_path, complete_title, description,
            options.category, options.keywords]
    kwargs = {
      "private": options.private,
      "location": parse_location(options.location),
      "unlisted": options.unlisted,
      "recorded": options.recorded,
      "nocomments": options.nocomments,
      "noratings": options.noratings,
    }
    if options.get_upload_form_data:
        data = youtube.get_upload_form_data(*args, **kwargs)
        return "\n".join([video_path, data["token"], data["post_url"]])
    elif options.api_upload or not pycurl:
        if not options.api_upload:
            debug("Install pycurl to upload the video using HTTP")
        debug("Start upload using basic gdata API: %s" % video_path)
        entry = youtube.upload_video(*args, **kwargs)
        url, video_id = get_entry_info(entry)
    else: # upload with curl
        data = youtube.get_upload_form_data(*args, **kwargs)
        entry = data["entry"]
        debug("Start upload using a HTTP post: %s -> %s" % (video_path, data["post_url"]))
        http_code, headers, body = post(data["post_url"], 
            {"file": video_path}, {"token": data["token"]}, 
            show_progressbar=not(options.hide_progressbar))
        if http_code != 302:
            raise UnsuccessfulHTTPResponseCode(
                "HTTP code on upload: %d (expected 302)" % http_code)
        params = dict(s.split("=", 1) for s in headers["Location"].split("?", 1)[1].split("&"))
        if params["status"] !=  "200":
            raise UnsuccessfulHTTPResponseCode(
                "HTTP status on upload link: %s (expected 200)" % params["status"])
        video_id = params["id"]
        url = "http://www.youtube.com/watch?v=%s" % video_id
    if options.wait_processing:
        wait_processing(youtube, video_id)
    return url

def run_main(parser, options, args, output=sys.stdout):
    """Run the main scripts from the parsed options/args."""
    if options.get_categories:
        output.write(" ".join(Youtube.get_categories().keys()) + "\n")
        return
    elif (options.create_playlist or options.add_to_playlist or 
         options.delete_from_playlist or options.update_metadata):
        required_options = ["email"]
    else:
        if not args:
            parser.print_usage()
            raise VideoArgumentMissing("Specify a video file to upload")
        required_options = ["email", "title", "category"]

    missing = [opt for opt in required_options if not getattr(options, opt)]
    if missing:
        parser.print_usage()
        raise OptionsMissing("Some required option are missing: %s" % ", ".join(missing))

    if options.password is None:
        password = getpass.getpass("Password for account <%s>: " % options.email)
    elif options.password == "-":
        password = sys.stdin.readline().strip()
    else:
        password = options.password
    youtube = Youtube(DEVELOPER_KEY)
    debug("Login to Youtube API: email='%s', password='%s'" %
          (options.email, "*" * len(password)))
    try:
        youtube.login(options.email, password, captcha_token=options.captcha_token,
                      captcha_response=options.captcha_response)
    except gdata.service.BadAuthentication:
        raise BadAuthentication("Authentication failed")
    except gdata.service.CaptchaRequired:
        token = youtube.service.captcha_token
        message = [
            "Captcha request: %s" % youtube.service.captcha_url,
            "Re-run the command with: --captcha-token=%s --captcha-response=CAPTCHA" % token,
        ]
        raise CaptchaRequired("\n".join(message))

    if options.create_playlist:
        title, description, private = tosize(options.create_playlist.split("|", 2), 3)
        playlist_uri = youtube.create_playlist(title, description, (private == "1"))
        debug("Playlist created: %s" % playlist_uri)
        output.write(playlist_uri+"\n")
    elif options.update_metadata:
        if not args:
            parser.print_usage()
            raise VideoArgumentMissing("Specify a video URL to upload")
        url = args[0]            
        updated = youtube.update_metadata(url, options.title, options.description, options.keywords)
        debug("Video metadata updated: %s" % url)
    elif options.add_to_playlist:
        for url in args:
            debug("Adding video (%s) to playlist: %s" % (url, options.add_to_playlist))
            video_id = get_video_id_from_url(url)
            youtube.add_video_to_playlist(video_id, options.add_to_playlist)
    elif options.delete_from_playlist:
        playlist = options.delete_from_playlist
        for url in args:
            video_id = get_video_id_from_url(url)
            debug("delete video (%s) from playlist: %s; video-id: %s" % 
              (url, playlist, video_id))
            youtube.delete_video_from_playlist(video_id, playlist)
    else:
      for index, video_path in enumerate(args):
        url = upload_video(youtube, options, video_path, len(args), index)
        output.write(url + "\n")

def main(arguments):
    """Upload video to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO_PATH ...

    Upload videos to youtube."""
    parser = optparse.OptionParser(usage, version=VERSION)

    # Required options
    parser.add_option('-m', '--email', dest='email', type="string",
        help='Authentication email or Youtube username')
    parser.add_option('-p', '--password', dest='password', type="string",
        help='Authentication password')
    parser.add_option('-t', '--title', dest='title', type="string",
        help='Video(s) title')
    parser.add_option('-c', '--category', dest='category', type="string",
        help='Video(s) category')

    # Side commands
    parser.add_option('', '--get-categories', dest='get_categories',
        action="store_true", default=False, help='Show video categories')
    parser.add_option('', '--create-playlist', dest='create_playlist', type="string",
        default=None, metavar="TITLE|DESCRIPTION|PRIVATE (0=no, 1=yes)",
        help='Create new playlist and add uploaded video(s) to it')

    # Optional options
    parser.add_option('-d', '--description', dest='description', type="string",
        help='Video(s) description')
    parser.add_option('', '--keywords', dest='keywords', type="string",
        help='Video(s) keywords (separated by commas: tag1,tag2,...)')
    parser.add_option('', '--title-template', dest='title_template', type="string",
        default="$title [$n/$total]", metavar="STRING",
        help='Title template to use on multiple videos (default: $title [$n/$total])')
    parser.add_option('', '--private', dest='private',
        action="store_true", default=False, help='Set uploaded video(s) as private')
    parser.add_option('', '--unlisted', dest='unlisted',
        action="store_true", default=False, help='Set uploaded video(s) as unlisted')
    parser.add_option('', '--nocomments', dest='nocomments',
        action="store_true", default=False, help='Disable comments for video(s)')
    parser.add_option('', '--noratings', dest='noratings',
        action="store_true", default=False, help='Disable ratings for video(s)')
    parser.add_option('', '--location', dest='location', type="string", default=None,
        metavar="LAT,LON", help='Video(s) location (lat, lon). example: "43.3,5.42"')
    parser.add_option('', '--recorded', dest='recorded', type="string", default=None,
        metavar="STRING", help='Video(s) recording time (YYYY-MM-DD). example: "2013-12-29"')
    parser.add_option('', '--update-metadata', dest='update_metadata', 
        action="store_true", default=False, help='Update video metadata (title/description)')

    # Upload options
    parser.add_option('', '--api-upload', dest='api_upload',
        action="store_true", default=False, help="Use the API upload instead of pycurl")
    parser.add_option('', '--get-upload-form-info', dest='get_upload_form_data',
        action="store_true", default=False, help="Don't upload, get the form info (PATH, TOKEN, URL)")
    parser.add_option('', '--hide-progressbar', dest='hide_progressbar',
        action="store_true", default=False, help="Hide progressbar on uploads")

    # Playlist options
    parser.add_option('', '--add-to-playlist', dest='add_to_playlist', type="string", default=None,
        metavar="URI", help='Add video(s) to an existing playlist')
    parser.add_option('', '--delete-from-playlist', dest='delete_from_playlist', type="string", default=None,
        metavar="URI", help='Delete video(s) from an existing playlist')
    parser.add_option('', '--wait-processing', dest='wait_processing', action="store_true",
        default=False, help='Wait until the video(s) has been processed')

    # Captcha options
    parser.add_option('', '--captcha-token', dest='captcha_token', type="string",
      metavar="STRING", help='Captcha token')
    parser.add_option('', '--captcha-response', dest='captcha_response', type="string",
      metavar="STRING", help='Captcha response')

    options, args = parser.parse_args(arguments)
    run_main(parser, options, args)

if __name__ == '__main__':
    sys.exit(catch_exceptions(EXIT_CODES, main, sys.argv[1:]))
