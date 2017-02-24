import requests
import re
import cache
import parsers

PAGEURL = "https://playoverwatch.com/en-us/career/{platform}{region}/{tag}"

def get_data(user, region, platform):
    data = find_user(user, region, platform)

    if not data:
        return None

    if data[1]:
        stats = data[1]
    else:
        page, region, battletag = data[0]
        stats = parsers.parse_stats(page, region, battletag, platform)
        cache.set(user + region + platform, stats, 1200)

    return stats

def find_user(battletag, region, platform):
    if not region:
        regions = ["us", "eu", "kr"]
    else:
        regions = [region]

    for reg in regions:
        cached = cache.get(battletag + reg + platform)
        if cached is not None:
            return None, cached

        user = get_user_page(battletag, reg, platform)

        if user is not None:
            return user, None
    else:
        return None


def get_user_page(battletag, region, platform):
    """
    Downloads a users playoverwatch.com page
    """

    reg = ("/" + region) if platform == 'pc' else ''

    url = PAGEURL.format(platform=platform, region=reg, tag=battletag)

    page = get_page(url)

    if not page:
        return None

    return (page, region, battletag)


def get_page(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.text


def parseInt(input):
    """
    Attempts to parse an int or return original
    """
    try:
        a = input.replace(",", "")
        return float(a)
    except:
        return input

HOUR_REGEX = re.compile(r"([0-9]*) hours?")
MINUTE_REGEX = re.compile(r"([0-9]*) minutes?")
SECOND_REGEX = re.compile(r"([0-9]*\.?[0-9]*) seconds?")
PERCENT_REGEX = re.compile(r"([0-9]{1,3})\s?\%")

def try_extract(value):
    """
    Attempt to extract a meaningful value from the time.
    """
    get_float = parseInt(value)
    # If it's changed, return the new int value.
    if get_float != value:
        return get_float

    # Next, try and get a time out of it.
    matched = HOUR_REGEX.match(value)
    if matched:
        val = matched.groups()[0]
        val = float(val)
        return val

    matched = MINUTE_REGEX.match(value)
    if matched:
        val = matched.groups()[0]
        val = float(val)
        val /= 60
        return val

    matched = SECOND_REGEX.match(value)
    if matched:
        val = matched.groups()[0]
        val = float(val)
        val = (val / 60 / 60)

        return val

    matched = PERCENT_REGEX.match(value)
    if matched:
        val = matched.groups()[0]
        val = float(val)
        val = (val / 100)

        return val

    # Check if there's an ':' in it.
    if ':' in value:
        sp = value.split(':')
        # If it's only two, it's mm:ss.
        if len(sp) == 2:
            mins, seconds = map(int, sp)
            hours = float(mins) / 60
            return hours

        # If it's three, it's hh:mm:ss.
        if len(sp) == 3:
            hours, mins, seconds = map(int, sp)
            mins = float(mins) / 60
            return hours + mins
    else:
        # Just return the value.
        return value
