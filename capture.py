#!/usr/bin/env python

import datetime
import json
import re
import pygame.camera
from pygame.locals import *
from dropbox import client, rest, session
import os
from optparse import OptionParser
import math
from gapi import get_latitude_info

DROPBOX_SECRETS = '/home/tina/dropbox_secrets.json'
DROPBOX_TOKEN_FILE = '/home/tina/dropbox_token_store.txt'
WEBCAM_PICTURE_FOLDER = '/home/tina/dashboard/static/img/webcam/'
HOME_GPS = '/home/tina/home_coordinate.json'
DISTANCE_TOLERANCE = 100
R = 6371000

def distance_between_two_gps_coordinates(gps1, gps2):
    lat1 = math.radians(gps1["latitude"])
    lon1 = math.radians(gps1["longitude"])
    lat2 = math.radians(gps2["latitude"])
    lon2 = math.radians(gps2["longitude"])
    return math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lon1 - lon2)) * R

def within_range():
    try:
        json_data = open(HOME_GPS)
        home_gps = json.load(json_data)
        json_data.close()
        position_info = json.loads(get_latitude_info())
        distance_tina = distance_between_two_gps_coordinates(position_info["tina"], home_gps)
        distance_eric = distance_between_two_gps_coordinates(position_info["eric"], home_gps)
        return distance_tina < 100 or distance_eric < 100
    except IOError as e:
        print "can't read home GPS info"

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

def take_picture_if_not_at_home():
    if within_range():
        return
    take_picture()

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
    parser = OptionParser()

    parser.add_option("-v", "--vacuum",
                      dest="vacuum",
                      action="store_true",
                      help="erase old pictures from dropbox")

    parser.add_option("-c", "--capture",
                      dest="capture",
                      action="store_true",
                      help="take a picture and store it in the /static/img/webcam directory")

    parser.add_option("-r", "--range",
                      dest="range",
                      action="store_true",
                      help="get tina and eric's position and return a bool to indicate whether we are at home")


    (options, args) = parser.parse_args()

    if options.vacuum:
        vacuum()
    elif options.capture:
        take_picture_if_not_at_home()
    elif options.range:
        print within_range()
    else:
        print parser.print_help()

