#!/usr/bin/env python

import sys
import urllib
import urllib2
import httplib
import json
from pprint import pprint
from optparse import OptionParser

GRAPH_URL = 'graph.facebook.com'
CLI_FILE = './cli.txt'


def get_access_token(app_id, app_secret):
    f = urllib2.urlopen("https://%s/oauth/access_token" \
            "?client_id=%s&client_secret=%s&grant_type=client_credentials" %
            (GRAPH_URL, app_id, app_secret))
    return f.read()


def load_users(app_id, access_token):
    f = urllib2.urlopen("https://%s/%s/accounts/test-users?%s" % \
                        (GRAPH_URL, app_id, access_token))
    return json.loads(f.read())['data']


def create_user(app_id, access_token, installed=None, permissions=None):
    data = {}
    if installed is not None:
        data['installed'] = installed
    if permissions is not None and len(permissions) > 0:
        data['permissions'] = permissions

    f = urllib2.urlopen("https://%s/%s/accounts/test-users?%s" % \
                        (GRAPH_URL, app_id, access_token),
                        data=urllib.urlencode(data))
    return json.loads(f.read())


def delete_user(user_id, access_token):
    conn = httplib.HTTPSConnection(GRAPH_URL)
    conn.request('DELETE', "/%s?%s" % (user_id, access_token))
    r = conn.getresponse()
    content = r.read()

    if content == 'true':
        return True
    else:
        return False


def modify_user(user_id, password):
    url = "https://%s/%s"

    try:
        d1 = {'access_token': user_id['access_token'], 'password': password}
        f1 = urllib2.urlopen(url % (GRAPH_URL, user_id['id']),
                             data=urllib.urlencode(d1))
        content = f1.read()

        if content == 'true':
            return 'New password of "%s" for %s set.' % \
                (password, user_id['id'])
        else:
            return 'Error:Password for %s not changed.' % (user_id['id'])
    except urllib2.HTTPError, e:
        error = json.loads(e.read())
        print error['error']['message']


def friend_users(user_1, user_2):
    url = "https://%s/%s/friends/%s"

    try:
        print "User 1 -> User 2...",
        d1 = {'access_token': user_1['access_token']}
        f1 = urllib2.urlopen(url % (GRAPH_URL, user_1['id'], user_2['id']),
                             data=urllib.urlencode(d1))
        r1 = f1.read()
        print "done."
    except urllib2.HTTPError, e:
        error = json.loads(e.read())
        print error['error']['message']

    try:
        print "User 2 -> User 1...",
        d2 = {'access_token': user_2['access_token']}
        f2 = urllib2.urlopen(url % (GRAPH_URL, user_2['id'], user_1['id']),
                             data=urllib.urlencode(d2))
        r2 = f2.read()
        print "done."
    except urllib2.HTTPError, e:
        error = json.loads(e.read())
        print error['error']['message']


def print_users(users):
    if len(users) == 0:
        print "No users."
        return

    print 'Users: '
    i = 1
    for user in users:
        token_str = 'No token.'
        if 'access_token' in user:
            token_str = user['access_token']

        print "  %s - %s:\n        login_url: %s\n        token: %s" % \
            (i, user['id'], user['login_url'], token_str)
        i += 1


def question(question, options):
    while True:
        options_str = '/'.join(options)
        answer = raw_input(" %s (%s): " % \
            (question, options_str)).strip().upper()
        if answer in options:
            return answer


def question_user(question):
    while True:
        try:
            user_num = int(raw_input(" %s #: " % question)) - 1
            user = users[user_num]
            return user
        except (IndexError, ValueError), e:
            print 'Invalid user number.'


if __name__ == '__main__':
    usage = "usage: %prog <app_id> <app_secret>"
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    if len(args) != 2:
        try:
            f = open(CLI_FILE)
            params = json.loads(f.readline())
            app_id = params['app_id']
            app_secret = params['app_secret']
            f.close()
        except Exception, e:
            parser.error('App ID and secret are required')
            sys.exit(1)
    else:
        app_id = args[0]
        app_secret = args[1]
        f = open(CLI_FILE, 'w')
        f.write(json.dumps({'app_id': app_id, 'app_secret': app_secret}))
        f.close()

    print 'Getting access token...',
    access_token = get_access_token(app_id, app_secret)
    print 'done.'

    print 'Getting user list...',
    users = load_users(app_id, access_token)
    print 'done.'

    while True:
        try:
            input = raw_input('Command (? for help): ')
            if len(input) != 0:
                cmd = input.strip()
                if cmd == '?':
                    print "Command action\n  a  Add user\n  l  List users\n" \
                          "m  Modify user\n  r  Reload user list\n" \
                          "d  Delete user\n  f  Friend users\n  q  Quit"
                elif cmd == 'a':
                    installed = question('Installed', ['Y', 'N'])
                    installed_options = {'Y': 'true', 'N': 'false'}
                    permissions = raw_input(' Permissions (comma seperated): ')
                    new_user = create_user(app_id,
                                           access_token,
                                           installed_options[installed],
                                           permissions)
                    users = load_users(app_id, access_token)
                    print "User added. email: {0}  password: {1}". \
                          format(new_user['email'], new_user['password'])
                elif cmd == 'l':
                    print_users(users)
                elif cmd == 'r':
                    users = load_users(app_id, access_token)
                    print "Done"
                elif cmd == 'f':
                    user_1 = question_user('First User')
                    user_2 = question_user('Second User')

                    if 'access_token' not in user_1 or \
                        'access_token' not in user_2:
                        print 'Both users need to have access tokens.'
                    elif user_1 == user_2:
                        print 'A user cannot befriend themselves. Tragic.'
                    else:
                        friend_users(user_1, user_2)
                elif cmd == 'd':
                    user = question_user('User')
                    r = delete_user(user['id'], access_token)
                    if r:
                        print 'User deleted.'
                    else:
                        print 'User not deleted.'
                    users = load_users(app_id, access_token)
                elif cmd == 'q' or cmd == 'quit' or cmd == 'exit':
                    sys.exit(1)

                elif cmd == 'm':
                    user_1 = question_user('User ')
                    password = raw_input("Enter Password: ").strip()
                    modify_result = modify_user(user_1, password)
                    print modify_result
                else:
                    print 'Unknown command.'
        except (EOFError, KeyboardInterrupt), e:
            sys.exit(1)
