#!/usr/bin/env python

import datetime
import json
import re
import pygame.camera
from pygame.locals import *
from dropbox import client, rest, session
import os

DROPBOX_SECRETS = '/home/tina/dropbox_secrets.json'
DROPBOX_TOKEN_FILE = '/home/tina/dropbox_token_store.txt'
WEBCAM_PICTURE_FOLDER = '/home/tina/dashboard/static/img/webcam/'

def authenticate_to_dropbox():
    try:
        # authenticate to dropbox
        json_data = open(DROPBOX_SECRETS)
        data = json.load(json_data)
        json_data.close()
        sess = StoredSession(data["key"], data["secret"], data["access_type"])
        api_client = client.DropboxClient(sess)
        sess.load_creds()
        return api_client

    except IOError as e:
        print "can't read dropbox secret file"

def take_picture():
    pygame.camera.init()
    cam = pygame.camera.Camera("/dev/video0", (640, 480))
    cam.start()
    image= cam.get_image()
    file_name = 'webcam%s.png' % datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    full_file_name = '%s%s' % (WEBCAM_PICTURE_FOLDER, file_name)
    pygame.image.save(image, full_file_name)
    cam.stop()
    # upload to dropbox
    client = authenticate_to_dropbox()
    f = open(full_file_name)
    response = client.put_file(file_name, f)
    print "uploaded: ", response
    return json.dumps('./static/img/webcam/%s' % file_name)

def vacuum():
    files = [f for f in os.listdir(WEBCAM_PICTURE_FOLDER) if os.path.isfile(os.path.join(WEBCAM_PICTURE_FOLDER, f))]
    for f in files:
        time_stamp = re.search('webcam(.+?).png', f).group(1)
        t = datetime.datetime.strptime(time_stamp, "%Y_%m_%d_%H_%M_%S")
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        # check if picture is too old
        if t < yesterday:
            os.remove('%s%s'% (WEBCAM_PICTURE_FOLDER, f))
            print "removing ", '%s%s'% (WEBCAM_PICTURE_FOLDER, f)
            # remove from dropbox
            client = authenticate_to_dropbox()
            response = client.file_delete(f)
            print "deleted: ", response

class StoredSession(session.DropboxSession):
    """a wrapper around DropboxSession that stores a token to a file on disk"""

    def load_creds(self):
        try:
            stored_creds = open(DROPBOX_TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print "[loaded access token]"
        except IOError:
            pass # don't worry if it's not there

    def write_creds(self, token):
        f = open(DROPBOX_TOKEN_FILE, 'w')
        f.write("|".join([token.key, token.secret]))
        f.close()

    def delete_creds(self):
        os.unlink(DROPBOX_TOKEN_FILE)

    def link(self):
        request_token = self.obtain_request_token()
        url = self.build_authorize_url(request_token)
        print "url:", url
        print "Please authorize in the browser. After you're done, press enter."
        raw_input()

        self.obtain_access_token(request_token)
        self.write_creds(self.token)

    def unlink(self):
        self.delete_creds()
        session.DropboxSession.unlink(self)

if __name__ == '__main__':
    # take_picture()
    vacuum()
