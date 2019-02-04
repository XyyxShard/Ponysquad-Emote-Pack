#!/usr/bin/python -tt

import copy
import json
import os
import requests
import shutil
import sys
import time
from io import BytesIO
from PIL import Image

EMOTE_URI = 'https://static-cdn.jtvnw.net/emoticons/v1/%d/2.0'

channels = [
    '27645199', # Vale
    '37524427', # LacedUpLauren
    '39940104', # EeveeA_
    '51533859', # AnneMunition
    '71963871', # Dead_Flip
]

def download_file(target, url, headers=None):
    headers = copy.deepcopy(headers)

    sys.stderr.write("Fetching '%s'... " % (url,))

    lastmod = None

    if os.path.exists(target):
        lastmod = os.stat(target).st_mtime

    if lastmod is not None:
        if headers is None:
            headers = {}
        headers['If-Modified-Since'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime(lastmod))

    try:
        req = requests.get(url, headers=headers, stream=True, timeout=5)
        req.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # uh oh.
        raise

    if req.status_code == 304:
        sys.stderr.write("ok (cached)\n")
        return True

    modified = req.headers.get('Last-Modified')
    if modified:
        modified = time.mktime(time.strptime(modified, "%a, %d %b %Y %H:%M:%S GMT"))

    with open(target + '.tmp', 'wb') as output:
        for chunk in req.iter_content(16384):
            output.write(chunk)

    shutil.move(target + '.tmp', target)
    if modified:
        os.utime(target, (modified, modified))

    sys.stderr.write("ok\n")
    return True

def fetch_emote(filename, url):
    r = requests.get(url)
    img = Image.open(BytesIO(r.content))
    img.thumbnail((40,40), Image.ANTIALIAS)
    img.save(filename)

    img = Image.open(BytesIO(r.content))
    img.thumbnail((120,120), Image.LANCZOS)
    img.save('hidpi/' + filename)

def get_subscriber_emotes():
    local_fname = 'subscriber-emotes.json'
    download_file(local_fname, 'https://twitchemotes.com/api_cache/v3/subscriber.json')
    with open(local_fname, 'rt') as fd:
        emotes = json.load(fd)
    return emotes

emotes = get_subscriber_emotes()

for channel in channels:
    if channel not in emotes:
        sys.stderr.write("Channel ID %s not found!\n" % (channel,))
        continue
    for emote in sorted(emotes[channel]['emotes'], key=lambda x: x['code']):
        fname = '%s.png' % (emote['code'],)
        emote_name = ':%s:' % (emote['code'],)
        emote_url = EMOTE_URI % (emote['id'],)
        fetch_emote(fname, emote_url)
        img = Image.open(fname)

        print("! %s %s %s" % (fname, emote_name, emote_name.lower()))
    print("")

# vim: set ts=4 sts=4 sw=4 et:
