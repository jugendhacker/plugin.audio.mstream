import sys
import urllib
import urlparse
import xbmcplugin
import xbmcgui
import xbmcaddon
import requests

print(sys.argv)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
this_addon= xbmcaddon.Addon()

def build_url(query):
    return base_url + '?' + urllib.urlencode(query, 'utf-8')

def play_song(path, token):
    item = xbmcgui.ListItem(path=this_addon.getSetting('server') + '/media/' + urllib.quote(path) + '?token=' + token)
    meta = requests.post(this_addon.getSetting('server') + '/db/metadata', data={'filepath': path, 'token': token}).json().get('metadata')
    info = {
        'artist': meta.get('artist'),
        'album': meta.get('album'),
        'tracknumber': meta.get('track'),
        'title': meta.get('title'),
        'year': meta.get('year')
    }
    item.setInfo('music', info)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=item)

response = requests.post(this_addon.getSetting('server') + '/login', data={'username': this_addon.getSetting('username'), 'password': this_addon.getSetting('password')}).json()
token = response.get('token')
folders = response.get('vpaths')

mode = args.get('mode')
if mode is None:
    xbmcplugin.setContent(addon_handle, 'files')
    url = build_url({'mode': 'files'})
    item = xbmcgui.ListItem('Files', iconImage='DefaultFolger.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'files':
    path = args.get('path')
    if path is None and len(folders) == 1:
        files = requests.post(this_addon.getSetting('server') + '/dirparser', data={'dir': folders[0], 'token': token}).json()
        for file in files.get('contents'):
            if(file.get('type') == 'directory'):
                url = build_url({'mode': 'files', 'path': files.get('path') + file.get('name')})
                item = xbmcgui.ListItem(file.get('name'), iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=True)
            else:
                url = build_url({'mode': 'play', 'path': files.get('path') + file.get('name')})
                item = xbmcgui.ListItem(file.get('name'))
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
    elif path is None and len(folders) > 1:
        for folder in folders:
            url = build_url({'mode': 'files', 'path': folder + '/'})
            item = xbmcgui.ListItem(folder, iconImage='DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)
    elif path is not None:
        files = requests.post(this_addon.getSetting('server') + '/dirparser', data={'dir': path[0], 'token': token}).json()
        for file in files.get('contents'):
            if(file.get('type') == 'directory'):
                url = build_url({'mode': 'files', 'path': files.get('path') + file.get('name')})
                item = xbmcgui.ListItem(file.get('name'), iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=True)
            else:
                url = build_url({'mode': 'play', 'path': files.get('path') + file.get('name')})
                item = xbmcgui.ListItem(file.get('name'))
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'play':
    play_song(args.get('path')[0], token=token)