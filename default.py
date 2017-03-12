# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urlparse
import json
import re

# plugin constants
USERAGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
addon = xbmcaddon.Addon()
__plugin__ = "plugin.video.sportube2"
__author__ = "Eugenio412"

Addon = xbmcaddon.Addon()

# plugin handle
handle = int(sys.argv[1])

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict

def notify(msg):
	xbmc.executebuiltin((u'Notification(%s,%s)' % (__plugin__ , msg)).encode('utf-8'))

def addLinkItem(url, li):
    return xbmcplugin.addDirectoryItem(handle=handle, url=url,
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu '''

    opener = urllib2.build_opener()
    # Use Firefox User-Agent
    opener.addheaders = [('User-Agent', USERAGENT)]
    urllib2.install_opener(opener)

    pageUrl = "http://sportube.tv/live"
    htmlData = urllib2.urlopen(pageUrl).read()
    match = re.compile('var base_url = "(.+?)"').findall(htmlData)
    baseUrl = match[0]
    match = re.compile('var API_KEY = "(.+?)"').findall(htmlData)
    apiKey = match[0]
    match = re.compile('var url_cdn = "(.+?)"').findall(htmlData)
    urlCdn = match[0]
    username = addon.getSetting('sportube_user')
    password = addon.getSetting('sportube_pass')
    #token
    url = baseUrl + "login?u="+ username + "&p=" + password + "&api_key=" + apiKey + "&force=true"
    headers = {'referer': pageUrl,
    'User-Agent': USERAGENT}
    try:
        request = urllib2.Request(url, headers = headers)
        data = urllib2.urlopen(request).read()
    except urllib2.HTTPError as e:
        notify(e.code)
    except urllib2.URLError as e:
        notify('URLError')
    else:
        # Convert JSONP object into JSON
        # https://stackoverflow.com/questions/30554522/django-parse-jsonp-json-with-padding
        data_json = data.split("(")[0].strip(")")
        token_json = json.loads(data_json)
        if "ERROR" in token_json:
            notify(token_json["ERROR"])
        else:
            token = token_json["token"]
            #liveEvents
            url = baseUrl + "tv.jsonp?callback=sportube_live_all&id=&api_key=" + apiKey
            headers = {'referer': pageUrl,
            'User-Agent': USERAGENT}
            try:
                request = urllib2.Request(url, headers = headers)
                data = urllib2.urlopen(request).read()
            except urllib2.HTTPError as e:
                notify(e.code)
            except urllib2.URLError as e:
                notify('URLError')
            else:
                # Convert JSONP object into JSON
                # https://stackoverflow.com/questions/30554522/django-parse-jsonp-json-with-padding
                data_json = data.split("(")[1].strip(")")
                liveEvents = json.loads(data_json)
                #livestream
                url = baseUrl + "live_events.jsonp?callback=sportube_live_events&id=&api_key=" + apiKey + "&days=7"
                headers = {'referer': pageUrl,
                'User-Agent': USERAGENT}
                request = urllib2.Request(url, headers = headers)
                data = urllib2.urlopen(request).read()
                data_json = data.split("(")[1].strip(")")
                liveStreams = json.loads(data_json)
                if "ERROR" in liveEvents:
                    notify("Error in tv.jsonp: " + liveEvents["ERROR"])
                elif "ERROR" in liveStreams:
                    notify("Error in live_events.jsonp: " + liveStreams["ERROR"])
                else:
                    # Parse video feed
                    for event in liveEvents["RESULT"]:
                        print(event)
                        linkId = event[9]
                        print(str(linkId))
                        for stream in liveStreams["RESULT"]:
                            if stream[0] == linkId:
                                #get stream
                                url = baseUrl + "manifest.m3u8?api_key" + apiKey + "&id=" + str(linkId) + "&token=" + token
                                headers = {'referer': pageUrl,
                                'User-Agent': USERAGENT}
                                try:
                                    request = urllib2.Request(url, headers = headers)
                                    data = urllib2.urlopen(request).read()
                                except urllib2.HTTPError as e:
                                    #notify(e.code)
                                except urllib2.URLError as e:
                                    notify('URLError')
                                else:
                                    data_json = data.split("#")[2].strip("\n")
                                    link = data_json[68:]
                                    imageUrl = event[2]
                                    title = event[1] + " - " + event[11] + " (" + event[10][11:16] + ") " + event[14] + " - " + event[15]
                                    liStyle = xbmcgui.ListItem(title, thumbnailImage=imageUrl)
                                    addLinkItem(link, liStyle)
                        break
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

show_root_menu()
