#!/usr/bin/env python
import httplib2
import datetime
from dateutil.parser import parse
import json

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

TINA_CALENDAR_ID = '/home/tina/calendar_id_tina.json'
ERIC_CALENDAR_ID = '/home/tina/calendar_id_eric.json'
TINA_CALENDAR_SECRETS = '/home/tina/calendar_tina.dat'
ERIC_CALENDAR_SECRETS = '/home/tina/calendar_eric.dat'
TINA_LATITUDE_SECRETS = '/home/tina/latitude_tina.dat'
ERIC_LATITUDE_SECRETS = '/home/tina/latitude_eric.dat'
TINA_TASKS_SECRETS = '/home/tina/tasks_tina.dat'
ERIC_TASKS_SECRETS = '/home/tina/tasks_eric.dat'

def build_service(secrets, service_tag, api_version):
    try:
        with open(secrets) as f: pass
    except IOError as e:
        print 'no client secret stored'
        return

    storage = Storage(secrets)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        print "we are in trouble. credential invalid!!!"
        credentials.refresh(httplib2.Http())

    http = httplib2.Http()
    http = credentials.authorize(http)
    return build(service_tag, api_version, http=http)

def get_calendar_info_for_person(calendar_secrets, calendar_id):
    """ Given the calendar secrets and id, finds the upcoming events
    in the following week. Returns a list of tuples, each of which is
    (start_time, end_time, summary)
    """
    service = build_service(calendar_secrets, 'calendar', 'v3')
    try:
        json_data = open(calendar_id)
        data = json.load(json_data)
        json_data.close()

        #find upcoming events
        events = service.events().list(calendarId=data["calendar_id"]).execute()
        # get all future events in the next week
        now = datetime.datetime.now()
        start_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = (now + datetime.timedelta(weeks=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        events = service.events().list(calendarId=data["calendar_id"], timeMin=start_time, timeMax=end_time).execute()
        return list((e['start'], e['end'], e['summary']) for e in events['items'])

    except AccessTokenRefreshError:
        credentials.refresh(httplib2.Http())
        print ('The calendar credentials have been revoked or expired')

def convert_to_datetime(datetime_dict):
    if 'dateTime' in datetime_dict:
        return parse(datetime_dict['dateTime']), False
    elif 'date' in datetime_dict:
        return parse(datetime_dict['date']), True

def format_event(event_info):
    label, start, end, summary = event_info
    start, no_start_time = convert_to_datetime(start)
    end, no_end_time = convert_to_datetime(end)
    date = start.strftime('%a, %b %d')
    time = 'All Day' if no_start_time and no_end_time else '{:%H:%M} - {:%H:%M}'.format(start, end)
    return {
        'date': date,
        'time': time,
        'summary': summary,
        'label': label
        }

def get_calendar_info():
    """
    1. Dedup the two calendars
    2. For each event, convert from start_time, end_time to date and time_span
    3. Append label for each event. The label is tina, eric, or both. Each event is turned into a dict
    """
    lst = list()
    tina_cal,  eric_cal = get_calendar_info_for_person(TINA_CALENDAR_SECRETS, TINA_CALENDAR_ID), get_calendar_info_for_person(ERIC_CALENDAR_SECRETS, ERIC_CALENDAR_ID)
    for start, end, summary in tina_cal:
        if (start, end, summary) in eric_cal:
            lst.append(('both', start, end, summary))
            tina_cal.remove((start, end, summary))
            eric_cal.remove((start, end, summary))
    [lst.append(('tina', start, end, summary)) for start, end, summary in tina_cal]
    [lst.append(('eric', start, end, summary)) for start, end, summary in eric_cal]
    return json.dumps([format_event(event) for event in sorted(lst, key=lambda x: x[1])])

def get_latitude_info_for_person(latitude_secrets):
    service = build_service(latitude_secrets, 'latitude', 'v1')
    try:
        cl = service.currentLocation()
        return cl.get(granularity="best").execute()

    except AccessTokenRefreshError:
        credentials.refresh(httplib2.Http())
        print ('The latitude credentials have been revoked or expired')

def get_latitude_info():
    return json.dumps({
            'tina': get_latitude_info_for_person(TINA_LATITUDE_SECRETS),
            'eric': get_latitude_info_for_person(ERIC_LATITUDE_SECRETS),
            })

def get_tasks_info_for_person(tasks_secrets):
    service = build_service(tasks_secrets, 'tasks', 'v1')
    try:
        tasks = service.tasks().list(tasklist='@default').execute()
        return list({'title': t['title'], 'due': t['due'] if 'due' in t else None} for t in tasks['items'] if 'title' in t and len(t['title']))

    except AccessTokenRefreshError:
        credentials.refresh(httplib2.Http())
        print ('The tasks credentials have been revoked or expired')

def format_task(task, label):
    return {
        'label': label,
        'title': task['title'],
        'due': task['due'],
        }

def get_tasks_info():
    tina_tasks = get_tasks_info_for_person(TINA_TASKS_SECRETS)
    eric_tasks = get_tasks_info_for_person(ERIC_TASKS_SECRETS)
    tasks = list()
    # dedup
    for task in tina_tasks:
        if task in eric_tasks:
            tasks.append(format_task(task, 'both'))
            eric_tasks.remove(task)
            tina_tasks.remove(task)
    [tasks.append(format_task(task, 'tina')) for task in tina_tasks]
    [tasks.append(format_task(task, 'eric')) for task in eric_tasks]
    tasks = sorted(tasks, key=lambda x: (x['due'] is None, x['due']))
    for task in tasks:
        if task['due']:
            task['due'] = parse(task['due']).strftime('%a, %b %d')
    return json.dumps(tasks)

if __name__ == '__main__':
    print get_tasks_info()
    # get_latitude_info(TINA_LATITUDE_SECRETS)
    # print get_calendar_info()
