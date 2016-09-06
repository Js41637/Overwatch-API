import requests
import cache

PAGEURL = "https://playoverwatch.com/en-us/career/{platform}{region}/{tag}"


def find_user(battletag, region, platform, version, method):
    if not region:
        regions = ["us", "eu", "kr"]
    else:
        regions = [region]

    for reg in regions:
        cached = cache.get(battletag + reg + platform + version + method)
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
    a = input.replace(",", "")
    try:
        return float(a)
    except ValueError:
        return a
