# diigo-backup

Backup Diigo bookmarks to a JSON file.

## Usage
python diigo-backup.py -v 0 -u USERNAME -a API_KEY -p PASSWORD > diigo-backup.json

## Options
* -h, --help
  show this help message and exit

* -u USER, --user=USER
  The user with which to connect

* -p PASSW, --pass=PASSW
  The given user's password

* -a APIKEY, --apikey=APIKEY
  API key (see https://www.diigo.com/api_keys/new/)

* -v 0-9, --verbosity=0-9
  Amount of output to show on screen
