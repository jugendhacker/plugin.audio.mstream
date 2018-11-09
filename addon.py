import sys
import urlparse
import urllib

import requests
import xbmcplugin
import xbmcgui
import xbmcaddon


DEFAULT_FOLDER = 'DefaultFolder.png'


class AddonOperator:
    def build_url(self, mode, path=None):
        query = {'mode': mode}
        if path is not None:
            query['path'] = path
        return self.base_url + '?' + urllib.urlencode(query, 'utf-8')

    def __init__(self, handle, base_url):
        self.handle = handle
        self.base_url = base_url
        addon = xbmcaddon.Addon()

        self.server = addon.getSetting('server')
        self.authenticate(addon.getSetting('username'), addon.getSetting('password'))

    def authenticate(self, username, password):
        auth_url = urlparse.urljoin(self.server, 'login')
        response = requests.post(auth_url, data={'username': username,
                                                 'password': password}).json()
        self.token = response['token']
        self.folders = response['vpaths']

    def add_item(self, name, url, icon=DEFAULT_FOLDER,
                 is_folder=False, properties=None):
        item = xbmcgui.ListItem(name, icon)

        if properties is not None:
            for name, value in properties.items():
                item.setProperty(name, value)

        xbmcplugin.addDirectoryItem(handle=self.handle,
                                    url=url,
                                    listitem=item,
                                    isFolder=is_folder)

    def build_filesystem(self):
        xbmcplugin.setContent(self.handle, 'files')
        self.add_item('Files',
                      url=self.build_url(mode='files'),
                      is_folder=True)
        xbmcplugin.endOfDirectory(self.handle)

    def list_folder_contents(self, folder):
        url = urlparse.urljoin(self.server, 'dirparser')
        response = requests.post(url, data={'dir': folder,
                                            'token': self.token}).json()
        for file in response['contents']:
            if file['type'] == 'directory':
                self.add_item(name=file['name'],
                              url=self.build_url(
                                  mode='files',
                                  path=response['path'] + file['name']
                              ),
                              is_folder=True)
            else:
                self.add_item(name=file['name'],
                              url=self.build_url(
                                  mode='play',
                                  path=response['path'] + file['name']
                              ),
                              icon=None,
                              properties={'IsPlayable': 'true'})
        xbmcplugin.endOfDirectory(self.handle)

    def list_folders(self, folders):
        for folder in folders:
            self.add_item(name=folder['name'],
                          url=self.build_url(mode='files', path=folder + '/'),
                          is_folder=True)
        xbmcplugin.endOfDirectory(self.handle)

    def play_song(self, path):
        song_meta_url = urlparse.urljoin(self.server, 'db/metadata')
        response = requests.post(song_meta_url, data={'filepath': path,
                                                      'token': self.token}).json()
        song_meta = response['metadata']

        song_url = urlparse.urljoin(self.server,
                                    'media/' + urllib.quote(path))
        item = xbmcgui.ListItem(
            path='{}?{}'.format(song_url, urllib.urlencode({'token': self.token}))
        )
        item.setInfo('music', {
            'artist': song_meta['artist'],
            'album': song_meta['album'],
            'tracknumber': song_meta['track'],
            'title': song_meta['title'],
            'year': song_meta['year']
        })
        xbmcplugin.setResolvedUrl(self.handle, succeeded=True, listitem=item)

    def act(self, mode, path):
        if mode is None:
            self.build_filesystem()
        elif mode[0] == 'files':
            if path is None and len(self.folders) == 1:
                self.list_folder_contents(self.folders[0])
            elif path is None and len(self.folders) > 1:
                self.list_folders(self.folders)
            else:
                self.list_folder_contents(path[0])
        elif mode[0] == 'play':
            self.play_song(path[0])


if __name__ == '__main__':
    print(sys.argv)

    base_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    args = urlparse.parse_qs(sys.argv[2][1:])

    operator = AddonOperator(addon_handle, base_url)
    operator.act(args.get('mode', None), args.get('path', None))
