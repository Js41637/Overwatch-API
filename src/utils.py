import requests
import re
import cache
import parsers

PAGEURL = "https://playoverwatch.com/en-us/career/{platform}{region}/{tag}"

def get_data_from_page_or_cache(user, region, platform):
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

    page = download_page(url)

    if not page:
        return None

    return (page, region, battletag)


def download_page(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.text


def parse_int(input, intpls):
    """
    Attempts to parse an int or return original
    """
    try:
        a = input.replace(",", "")
        if intpls:
            return int(a)
        return float(a)
    except:
        return input
