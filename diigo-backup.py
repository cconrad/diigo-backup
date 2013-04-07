#!/usr/bin/python
"""
diigo.py - a utility for backing up Diigo bookmarks.
"""

# Copyright (c) 2013 Claus Conrad <http://www.clausconrad.com/>
# Based on code (c) 2008 Kliakhandler Kosta <Kliakhandler@Kosta.tk>

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

import urllib2 # For interacting with the Diigo servers
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

def getUserBookmarks(username, apikey):
    """
    Takes a username from which to extract the bookmarks
    and the application's API key.
    Returns the user's bookmarks in JSON format.

    This function does not handle authentication and therefore
    urllib2 should be set up correctly in advance (see
    "basicAuthSetup" method)
    """

    response = ''
    json = '[]'
    start = 0
    # The Diigo API returns up to 100 bookmarks at a time.
    # Therefore we iterate until we stop getting bookmarks.
    while response != '[]':
        json = json[:-1] + response[1:-1] + ',' + json[-1:]

        # Get the bookmarks in json format from the Diigo api
        Log("Getting 100 bookmarks starting from position "
        + str(start), DEBUG)
        bookmarks = urllib2.urlopen(BOOKMARKS_URL + '?user=' + username
            +'&start=' + str(start) + '&key=' + apikey + '&filter=all&count=100')
        response = bookmarks.read()
        Log("Response: \n" + response, FULL)

        # Wait a little to not choke the api servers, then get the next 100
        time.sleep(2)
        start += 100

    # Remove pre- or appended comma
    if json[1:2] == ",":
        json = json[0:1] + json[2:]
    if json[-2:-1] == ",":
        json = json[:-2] + json[-1:]
    return json


def main():
    (options, args) = commandlineOptions()

    # Set verbosity level which will be used
    # to determine the amount of output to print.
    if options.verbosity:
        setverbosity(int(options.verbosity))
    else:
        setverbosity(INFO)

    # Set up urllib2 to authenticate with the user's credentials.
    basicAuthSetup(options.username, options.password, API_SERVER)
    Log("Set basic authentication with following credentials:\n" +
        "User: " + options.username + " Password: " + options.password,
        DEBUG)
    try:
        bookmarks = getUserBookmarks(options.username, options.apikey)
    except urllib2.HTTPError, inst:
        bookmarks = None
        FatalError("Error: " + str(inst) + "\n" + inst.read())

    Log("Bookmarks retrieved:\n" + str(bookmarks), FULL)
    Log("Retrieved " + str(len(bookmarks)) + " bookmarks.", INFO)

    print bookmarks


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
    Defines and parses the command line options.
    """
    parser = OptionParser()
    parser.add_option("-u", "--user", dest="username",
        help="The user with which to connect",
        metavar="USER")
    parser.add_option("-p", "--pass", dest="password",
        help="The given user's password",
        metavar="PASSW")
    parser.add_option("-a", "--apikey", dest="apikey",
        help="API key (see https://www.diigo.com/api_keys/new/)",
        metavar="APIKEY")
    parser.add_option("-v", "--verbosity", dest="verbosity",
        help="Amount of output to show on screen",
        metavar="0-9")

    (options, args) = parser.parse_args()

    if not options.username or not options.password or not options.apikey:
        parser.print_help()
        sys.exit(1)

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