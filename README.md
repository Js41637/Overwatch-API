# Overwatch Python API
API for fetching Overwatch Stats

Original and core code from https://github.com/SunDwarf/OWAPI

I wrote my own version in Python 2.7 so I could run it on Windows and make some of my own changes.

API hosts it's own docs on `/`

This API returns both QuickPlay and Competitive Stats (if any) in the one request and the same goes for the heroes.

## Installation
This is written using Python 2.7 and only has 3 dependencies, Flask, lxml and requests

#### Install the required package dependencies
```pip install -r requirements.txt```

## Usage
##### Dev Mode
```python main.py```

## Todo
 * Cache requests

## Hosting
I host using Google App Engine, it's free and you can directly upload the src just remove the following code from from `main.py`
```
if __name__ == '__main__':
    app.run(debug=True, host='localhost')
```
