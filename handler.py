import sys

# Import local dependencies
sys.path.append('./site-packages')

import os
import datetime
import json
import traceback
import dateutil.parser
from pprint import pprint
import requests

######################################################
#
# Date Utils
#
######################################################

def df(d):
    """Format date in human readable format"""
    sf = ''
    try:
        sf = d.strftime('%b %d, %Y %H:%M:%S')
    except Exception as e:
        print(e)
    return sf

def dfiso(d):
    """Format date in ISO"""
    sf = ''
    try:
        sf = d.strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        print(e)
    return sf

def dp(dstr):
    """Create date object from string"""
    d = None
    try:
        d = dateutil.parser.parse(dstr)
    except Exception as e:
        print(e)
    return d

def dt(ts):
    """Create UTC date from timestamp"""
    d = None
    try:
        d = datetime.datetime.utcfromtimestamp(float(ts))
    except Exception as e:
        print(e)
    return d

######################################################
#
# General Utils
#
######################################################

def pp(o):
    """Custom pretty print"""
    print((json.dumps(o, indent=2, sort_keys=True)))

def request_error(req):
    """Custom errpr printing for Requests library"""
    print('HTTP Status %s ' % req.status_code)
    print(req.text)
    print(req.headers)


######################################################
#
# Common
#
######################################################

def get(api_url, access_token, path):
    """Wrapper method for API calls"""
    url = api_url + path
    if '?' not in url:
        url = url + '?'
    url = url + '&auth_token=' + access_token
    try:
        print('Calling: ' + url)
        r = requests.get(url)
        valid = r.status_code >= 200 and r.status_code < 400
        if not valid:
            if r.status_code == 429:
                json_data = r.json()
                print(json_data['error']['message'])
        else:
            json_data = r.json()
            #pprint(json_data) 
        return (valid, r)
    except ValueError as e:
        print(e)
        request_error(r)
    except requests.exceptions.SSLError as e:
        print(e)
    return None

######################################################
#
# Hipchat logic
#
######################################################

def get_user_id(api_url, access_token):
    """Check access token validity and get user id
       https://www.hipchat.com/docs/apiv2/method/get_session"""
    print('Getting user info ...')
    if access_token:
        path = 'oauth/token/' + access_token
        valid, r = get(api_url, access_token, path)
        json_data = r.json()
        return json_data['owner']['id']
    return False

def get_auto_join_rooms(api_url, access_token, id_or_email):
    """Get the list of rooms the user has subscribed to"""
    print('Getting auto-join rooms ...')
    path = 'user/%s/preference/auto-join?expand=items&max-results=1000' % id_or_email
    rooms = {}
    valid, r = get(api_url, access_token, path)
    if valid:
        json_data = r.json()
        rooms = json_data['items']
        print('rooms', len(rooms))
    else:
        request_error(r)
    return rooms

def get_users(api_url, access_token):
    """Get the list of individual users the user has had conversations with"""
    print('Getting users ...')
    path = 'user?expand=items&max-results=1000'
    users = {}
    valid, r = get(api_url, access_token, path)
    if valid:
        json_data = r.json()
        users = json_data['items']
        print('users', len(users))
    else:
        request_error(r)
    return users

def get_info_for_xmpp(rooms, users, xmpp_id):
    """Utility to find a user/room by xmpp id
       Returns: (id, idtype, name, email)"""
    for r in rooms:
        if r['xmpp_jid'] == xmpp_id:
            return (r['id'], 'room', r['name'], None)
    for u in users:
        if u['xmpp_jid'] == xmpp_id:
            return (u['id'], 'user', u['name'], u['email'])
    return (None, None, None, None)

def unread_room(api_url, access_token, id_or_name, name, mid):
    """Search for last unread message in a room
       Searches for the last read message and 
       then checks if there are any newer messages"""
    print('Checking unread_room: %s' % name)
    path = 'room/%s/history/latest' % id_or_name
    valid, r = get(api_url, access_token, path)
    items = []
    if valid:
        found = False
        newer = False
        json_data = r.json()
        for item in json_data['items']:
            id = item['id']
            dutc = dp(item['date'])
            msg = item['message']
            fr = item['from']
            if fr:
                try:
                    uname = fr['name']
                except TypeError as e:
                    uname = fr
            if found:
                newer = True
            else:
                found = (id == mid)
            if found and not newer:
                print('  Read: %s on %s by %s: %s' % (id, df(dutc), uname, msg))
                items.append('%s: %s\n%s' % (uname, df(dutc), msg))
            if newer:
                print('  Unread: %s on %s by %s' % (id, df(dutc), uname))
                items.append('%s: %s\n%s' % (uname, df(dutc), msg))
        #if len(items) > 0:
            #logger.info('  %s: %s new.' % (name, len(items)))
    else:
        request_error(r)
    return items

def unread_user(api_url, access_token, id_or_email, name, mid):
    """Search for last unread message in a user chat
       Searches for the last read message and 
       then checks if there are any newer messages"""
    print('Checking unread_user: %s' % name)
    path = 'user/%s/history/latest' % id_or_email
    valid, r = get(api_url, access_token, path)
    items = []
    if valid:
        found = False
        newer = False
        json_data = r.json()
        for item in json_data['items']:
            id = item['id']
            dutc = dp(item['date'])
            msg = item['message']
            fr = item['from']
            if fr:
                try:
                    uname = fr['name']
                except TypeError as e:
                    uname = fr
            if found:
                newer = True
            else:
                found = (id == mid)
            if found and not newer:
                print('  Read: %s on %s by %s: %s' % (id, df(dutc), uname, msg))
                items.append('%s: %s\n%s' % (uname, df(dutc), msg))
            if newer:
                print('  Unread: "%s on %s by %s' % (id, df(dutc), uname))
                items.append('%s: %s\n%s' % (uname, df(dutc), msg))
    else:
        request_error(r)
    return items

def get_unread_summary(api_url, access_token, rooms, users):
    """Calls undocumented API to get last read messages
       and then search for newer messages in rooms and user chats"""
    print('Searching for unread messages ...')
    path= 'readstate?expand=items.unreadCount'
    valid, r = get(api_url, access_token, path)
    items = []
    i = 0
    if valid:
        json_data = r.json()
        for item in json_data['items']:
            mid = item['mid']
            ts = item['timestamp']
            d = dt(ts)
            xmpp_id= item['xmppJid']
            id, idtype, name, email = get_info_for_xmpp(rooms, users, xmpp_id)
            if id:
                i=i+1
            print('## Unread Room | User: %s. %s %s (%s): %s (%s) %s' % (i, name, id, xmpp_id, df(d), ts, mid))
            unread_items = []
            if id:
                if idtype == 'room':
                    print('  Room: %s. %s %s' % (i, idtype.capitalize(), name))
                    unread_items = unread_room(api_url, access_token, id, name, mid)
                if idtype =='user':
                    print('  User: %s. %s %s' % (i, idtype.capitalize(), name))
                    unread_items = unread_user(api_url, access_token, id, name, mid)
                if len(unread_items) > 0:
                    unread_obj = {
                        "name": name,
                        "messages": '\n'.join(unread_items)
                    }
                    items.append(unread_obj)
                else:
                    print('No user or room id found for xmpp_id: %s' % xmpp_id)
    print('Done checking %s rooms/conversations.' % i)
    return items

######################################################
#
# Lambda functions
#
######################################################

def unread(event, context):
    """Lambda method to return unread message summary
       API TTL cache set to support Hipchat API rate limits"""
    response = {
        'statusCode': 200,
        'body': ''
    }
    pp(event)

    access_token = None
    items = []

    try:
        access_token = event['queryStringParameters']['access_token']
    except:
        try:
            access_token = event['headers']['x-access-token']
        except Exception as e:
            access_token = None

    if access_token:
        api_url = os.environ['HIPCHAT_API_URL']
        print('HIPCHAT_API_URL', api_url)
        try:
            user_id = get_user_id(api_url, access_token)
            print('user_id', user_id)

            rooms = get_auto_join_rooms(api_url, access_token, user_id)
            users = get_users(api_url, access_token)
            items = get_unread_summary(api_url, access_token, rooms, users)
        except Exception as e:
            print(traceback.format_exc())
            items = [{'name': 'Error', 'messages': str(e)}]
    else:
       items = [{'name': 'Error', 'messages': 'No Hipchat Access Token supplied'}]

    response['body'] = json.dumps(items)
    pprint(items)

    return response
