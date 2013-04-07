#!/usr/bin/python
"""
diigo.py - a library and utility for manipulating diigo bookmarks.
depends on demjson - http://deron.meranda.us/python/demjson/
"""

# Copyright (c) 2008 Kliakhandler Kosta <Kliakhandler@Kosta.tk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import demjson # for encoding/decoding json<->python
import urllib2 # For interacting with the diigo servers
import urllib # For encoding queries to be transmitted via POST
import time # For waiting between queries
import sys # For the logging methods.
from optparse import OptionParser # For parsing commandline options.

# Constants:
API_SERVER = "secure.diigo.com"
BOOKMARKS_URL = "https://secure.diigo.com/api/v2/bookmarks"
INFO=3
DEBUG=6
FULL=9
# /Constants

def getUserBookmarks(username):
    """
    Takes a username from which to extract the bookmarks.
    Optionaly takes a password to extract private bookmarks.
    Returns a list with the user's bookmarks.

    This function does not handle authentication and therefore
    urllib2 should be set up correctly in advance.
    """

    response = ''
    json = '[]'
    start = 0
    # The diigo api returns up to 100 bookmarks at a time.
    # Therefore we iterate until we stop getting bookmarks.
    while response != '[]':
        json = json[:-1] + response[1:-1] + json[-1:]

        # Get the bookmarks in json format from the diigo api
        Log("Getting 100 bookmarks starting from position "
        + str(start), DEBUG)
        bookmarks = urllib2.urlopen(BOOKMARKS_URL + '?user=' + username
                                    +'&start=' + str(start))
        response = bookmarks.read()
        Log("Response: \n" + response, FULL)

        # Wait a little to not choke the api servers, then get the next 100
        time.sleep(2)
        start += 100

    # Turns the json string bookmark array into a python
    # dict object and returns it.
    return demjson.decode(json)


def addUserBookmarks(username, bookmarks):
    """
    Takes a username for which we are adding bookmarks and list
    containint the bookmarks to be added.

    This function does not handle authentication and therefore
    urllib2 should be set up correctly in advance.
    """

    Log("Formatting bookmarks for sending", DEBUG)
    for bookmark in bookmarks:
        # Delete unnecessary fields to conserve bandwidth.
        # The diigo api ignores them at the moment.
        if bookmark['user']: del bookmark['user']
        if bookmark['created_at']: del bookmark['created_at']
        if bookmark['updated_at']: del bookmark['updated_at']

        if type(bookmark) == dict:
            # The diigo api requires the tag list to be a comma seperated
            # string, so if it is a dict we parse and format it
            tags = ''
            for tag in bookmark['tags']:
                tags += tag + ', '
            else:
                tags = tags[:-2]
            bookmark['tags'] = tags

    # The diigo api only allows to add up to 100 bookmarks at a time
    # so we iterate and send 100 bookmarks each time.
    iterations = len(bookmarks)/100 + 1

    Log("Submitting bookmarks to diigo", DEBUG)
    for range_index in range(iterations):
        # Take 100 bookmarks or what's left when there is less then 100
        if range_index == iterations - 1:
            partial_bookmarks = bookmarks[range_index*100 : ]

        else:
            partial_bookmarks = bookmarks[range_index*100 :
            (range_index+1)*100]

        Log("Iteration " + str(range_index) + " Of " +
            str(iterations), DEBUG)
        Log("The python list:\n" + str(partial_bookmarks), FULL)

        # Turn the list into json for sending over http
        json = demjson.encode(partial_bookmarks)
        Log("The json to be sent:\n" + json, FULL)

        # Encode the json into a safe format for transmission
        data = urllib.urlencode({'bookmarks':json})
        Log("The url-encoded data to be sent:\n" + data, FULL)

        # Submit the bookmark
        response = urllib2.urlopen(BOOKMARKS_URL, data)
        Log("Server response: " + response.read(), DEBUG)

        # Sleep a little to not load up the api servers
        time.sleep(2)

    return len(bookmarks)


def main():
    (options, args) = commandlineOptions()

    # Set verbosity level which will be used
    # to determine the amount of output to print.
    if options.verbosity:
        setverbosity(int(options.verbosity))
    else:
        setverbosity(INFO)

    # Set up urllib2 to authenticate with the old user's credentials.
    basicAuthSetup(options.username, options.password, API_SERVER)
    Log("Set basic authentication with following credentials:\n" +
        "User: " + options.username + " Password: " + options.password,
        DEBUG)
    try:
        bookmarks = getUserBookmarks(options.username)
    except urllib2.HTTPError, inst:
        FatalError("Error: " + str(inst) + "\n" + inst.read())

    Log("Bookmarks retrieved:\n" + str(bookmarks), FULL)
    Log("Retrieved " + str(len(bookmarks)) + " bookmarks.", INFO)

    # Set up urllib2 to authenticate with the new user's credentials.
    basicAuthSetup(options.newuser, options.newpassword, API_SERVER)
    Log("Set basic authentication with following credentials:\n" +
        "User: " + options.newuser + " Password: " + options.newpassword,
        DEBUG)

    try:
        # Add the bookmarks to the new user and print the result:
        Log("Added " + str(addUserBookmarks(options.newuser, bookmarks)) +
            " bookmarks", 3)
    except urllib2.HTTPError, inst:
        FatalError("Error: " + str(inst) + "\n" + inst.read())


def basicAuthSetup(user, password, naked_url):
    """
    Sets up urllib2 to automatically use basic authentication
    in the supplied url (which is supplied w/o the protocol)
    using the supplied username and password
    """
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

    # This will use the supplied user/password for all
    # child urls of naked_url because of the 'None' param.
    passman.add_password(None, naked_url, user, password)

    # This creates and assigns a custom authentication handler
    # for urllib2, which will be used when we call urlopen.
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)


def commandlineOptions():
    """
    Defines an parrses the command line options.
    """
    parser = OptionParser()
    parser.add_option("-u", "--user", dest="username",
        help="The user with which to connect",
        metavar="USER")
    parser.add_option("-p", "--pass", dest="password",
        help="The given user's password",
        metavar="PASSW")
    parser.add_option("-n", "--newuser", dest="newuser",
        help="The new user for the bookmarks",
        metavar="NEWUSER")
    parser.add_option("-e", "--newpassword", dest="newpassword",
        help="The password for the new user",
        metavar="NEWPASS")
    parser.add_option("-v", "--verbosity", dest="verbosity",
        help="Amount of output to show on screen",
        metavar="0-9")

    (options, args) = parser.parse_args()
    return (options, args)


#==== Logging methods ====#
# Logging methods taken from duplicity - http://www.nongnu.org/duplicity/

verbosity = 3
termverbosity = 3

def Log(s, verb_level):
    """Write s to stderr if verbosity level low enough"""
    if verb_level <= termverbosity:
        if verb_level <= 2:
            sys.stderr.write(s + "\n")
            sys.stderr.flush()
        else:
            sys.stdout.write(s + "\n")
            sys.stdout.flush()

def Warn(s):
    """Shortcut used for warning messages (verbosity 2)"""
    Log(s, 2)

def FatalError(s):
    """Write fatal error message and exit"""
    sys.stderr.write(s + "\n")
    sys.stderr.flush()
    sys.exit(1)

def setverbosity(verb, termverb = None):
    """Set the verbosity level"""
    global verbosity, termverbosity
    verbosity = verb
    if termverb: termverbosity = termverb
    else: termverbosity = verb

#====/Logging methods====#

if __name__ == "__main__":
    main()