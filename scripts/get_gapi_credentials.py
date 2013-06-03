#!/usr/bin/python

import httplib2
import sys

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

client_id = sys.argv[1]
client_secret = sys.argv[2]
credentials_path = sys.argv[3]

# scope = 'https://www.googleapis.com/auth/calendar'
scope = 'https://www.googleapis.com/auth/tasks'
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.82 Safari/537.1'
access_type = 'offline'

flow = OAuth2WebServerFlow(client_id, client_secret, scope, user_agent=user_agent, access_type=access_type)

def main():
  storage = Storage(credentials_path)
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(flow, storage)

  http = httplib2.Http()
  http = credentials.authorize(http)
  credentials.refresh(http)

if __name__ == '__main__':
  # call this function like 'python get_gapi_credentials.py client_id client_secret credentials_path'
  main()
