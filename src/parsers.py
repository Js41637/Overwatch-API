from lxml import etree
import utils
import datastore

def parse_stats(mode, page, region, battletag, version):
    if version == 'both':
        data = {"player": {}, "stats": { "quickplay": {}, "competitive": {}}}
    elif version == 'quickplay':
        data = {"player": {}, "stats": { "quickplay": {}}}
    elif version == 'competitive':
        data = {"player": {}, "stats": { "competitive": {}}}
    else:
        data = {"player": {}}

    parsed = etree.HTML(page)

    data["player"]["battletag"] = battletag
    data["player"]["region"] = region
    data["player"]["level"] = int(parsed.find(".//div[@class='player-level']/div").text)
    data["player"]["avatar"] = parsed.find(".//img[@class='player-portrait']").attrib['src']

    # Try and fetch Comp Rank
    hasrank = parsed.findall(".//div[@class='competitive-rank']/div")
    if hasrank:
        data["player"]["comprank"] = int(hasrank[0].text)
    else:
        data["player"]["comprank"] = None

    # Try and fetch Rank
    rank = parsed.xpath(".//div[@class='player-level']")[0]
    try:
        bg_image = [x for x in rank.values() if 'background-image' in x][0]
    except IndexError:
        data["player"]["rank"] = 0
    else:
        for key, val in datastore.ranks.items():
            if key in bg_image:
                data["player"]["rank"] = val
                break
        else:
            # Unknown Rank
            data["player"]["rank"] = None

    if mode == 'basic':
        return data

    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='0x02E00000FFFFFFFF']")

    #Stats contains both Quick and Comp, if no comp, set it to Null
    if len(stats) != 2:
        if version == 'competitive':
            return {"error": True, "msg": "No competitive stats"}
        elif version == 'both':
            data["stats"]["competitive"] = None

    # Go through both QuickPlay and Competetive stats
    for i, item in enumerate(stats):
        if (version == 'competitive' and i == 0) or (version == 'quickplay' and i == 1):
            continue

        stat_groups = item

        overall_stats = {}
        game_stats = {}
        featured_stats = []

        game_box = stat_groups[6]

        # Fetch Overall stats
        w = game_box.xpath(".//text()[. = 'Games Won']/../..")
        if not w:
            wins = 0
        else:
            wins = int(w[0][1].text.replace(",", ""))

        g = game_box.xpath(".//text()[. = 'Games Played']/../..")
        if not g:
            wr, losses, games = 0, 0, 0
        else:
            games = int(g[0][1].text.replace(",", ""))
            wr = round(((float(wins) / games)), 1)
            losses = games - wins

        overall_stats["wins"] = wins
        overall_stats["win_rate"] = wr
        overall_stats["losses"] = losses
        overall_stats["games"] = games

        # Fetch Game Stats
        average_stats = {}
        for subbox in stat_groups:
            stats = subbox.findall(".//tbody/tr")
            for stat in stats:
                name, value = stat[0].text.lower().replace(" ", "_").replace("_-_", "_"), stat[1].text
                amount = utils.parseInt(value)
                if 'average' in name.lower():
                    # Don't include average stats in the game_stats, use them for the featured stats section
                    average_stats[name.replace("_average", "")] = amount
                else:
                    game_stats[name] = amount

        # Manually add KPD
        game_stats["kpd"] = round(game_stats["eliminations"] / game_stats["deaths"], 2)

        # Generate Featured Stats
        for astat in average_stats:
            if average_stats[astat] != 0:
                if astat[:-1] in game_stats:
                    featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": game_stats[astat[:-1]]})
                else:
                    featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": game_stats[astat]})


        if i == 0:
            data["stats"]["quickplay"] = {"featured_stats": featured_stats, "game_stats": game_stats, "overall_stats": overall_stats}
        else:
            data["stats"]["competitive"] = {"featured_stats": featured_stats, "game_stats": game_stats, "overall_stats": overall_stats}

    return data

def parse_heroes(page, region, battletag, version):
    if version == 'both':
        data = {"quickplay": [], "competitive": []}
    elif version == 'quickplay':
        data = {"quickplay": []}
    elif version == 'competitive':
        data = {"competitive": []}

    parsed = etree.HTML(page)
    stats = parsed.xpath(".//div[@data-category-id='overwatch.guid.0x0860000000000021']")

    for i, item in enumerate(stats):
        if (version == 'competitive' and i == 0) or (version == 'quickplay' and i == 1):
            continue

        built_heroes = []
        heroes = item.xpath(".//div[@class='bar-text']")
        for ii, hero in enumerate(heroes):
            htime = hero.find(".//div[@class='description']").text
            # If the first hero has no playtime then we can assume that none have been played
            # and that they haven't played comp mode so we will ignore all the rest
            if htime == '--':
                if ii == 0 and i == 1:
                    if version == 'competitive':
                        return {"error": True, "msg": "No competitive stats"}
                    break
                else:
                    htime = '0'
            hname = hero.find(".//div[@class='title']").text
            cname = hname.replace(".", "").replace(": ", "").replace(u"\xfa", "u").replace(u'\xf6', 'o')

            built_heroes.append({"name": hname, "time": htime, "extended": '/hero/' + cname.lower()})

        if i == 0:
            data["quickplay"] = built_heroes
        else:
            data["competitive"] = built_heroes

    return data

def parse_hero(page, region, battletag, hero, version):
    if version == 'both':
        data = {"quickplay": {}, "competitive": {}}
    elif version == 'quickplay':
        data = {"quickplay": {}}
    elif version == 'competitive':
        data = {"competitive": {}}

    heroid = datastore.heroes[hero]["id"]

    data["name"] = datastore.heroes[hero]["name"]

    parsed = etree.HTML(page)
    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='{0}']".format(heroid))

    if len(stats) == 0:
        return {"error": True, "msg": "User has no stats for this hero"}

    #Stats contains both Quick and Comp, if no comp, set it to Null
    if len(stats) != 2:
        if version == 'competitive':
            return {"error": True, "msg": "No competitive stats"}
        elif version == 'both':
            data["competitive"] = None

    # Go through both QuickPlay and Competetive stats
    for statsIndex, item in enumerate(stats):
        if (version == 'competitive' and statsIndex == 0) or (version == 'quickplay' and statsIndex == 1):
            continue

        hero_stats = {}
        general_stats = {}
        featured_stats = []
        overall_stats = {}
        average_stats = {}

        hbtitle = item[0].find(".//span[@class='stat-title']").text
        if hbtitle == 'Hero Specific':
            hero_box = item[0]
            startingPos = 1
        else:
            hero_box = None
            startingPos = 0

        # Find the Game Box as it can change location
        for itemIndex, subbox in enumerate(item[startingPos:]):
            title = subbox.find(".//span[@class='stat-title']").text
            if title == 'Game':
                game_box = item[itemIndex + 1]
                break
        else:
            game_box = None

        # Fetch Overall stats
        if game_box is not None:
            wins = game_box.xpath(".//text()[. = 'Games Won']/../..")
            games = game_box.xpath(".//text()[. = 'Games Played']/../..")
            overall_stats["wins"] = int(wins[0][1].text.replace(",", "")) if len(wins) != 0 else None
            overall_stats["games"] = int(games[0][1].text.replace(",", "")) if len(games) != 0 else None
            if overall_stats["wins"] is not None and overall_stats["games"] is not None:
                overall_stats["win_rate"] = round(((float(overall_stats["wins"]) / overall_stats["games"])), 1)
                overall_stats["losses"] = overall_stats["games"] - overall_stats["wins"]
            else:
                overall_stats.update({"win_rate": None, "losses": None})
        else:
            overall_stats = {'wins': None, 'win_rate': None, 'losses': None, 'games': None}

        # Fetch Hero Specific Stats
        if hero_box is not None:
            for hstat in hero_box.findall(".//tbody/tr"):
                name, value = hstat[0].text.lower().replace(" ", "_").replace("_-_", "_"), hstat[1].text
                amount = utils.parseInt(value)
                if 'average' in name.lower():
                    # Don't include average stats in the general_stats, use them for the featured stats section
                    average_stats[name.replace("_average", "")] = amount
                else:
                    hero_stats[name] = amount

        # Fetch General Hero Stats
        for subbox in item[startingPos:]:
            stats = subbox.findall(".//tbody/tr")
            for stat in stats:
                name, value = stat[0].text.lower().replace(" ", "_").replace("_-_", "_"), stat[1].text
                amount = utils.parseInt(value)
                if 'average' in name.lower():
                    # Don't include average stats in the general_stats, use them for the featured stats section
                    average_stats[name.replace("_average", "")] = amount
                else:
                    general_stats[name] = amount

        # Manually add KPD
        if 'eliminations' in general_stats and 'deaths' in general_stats:
            general_stats["kpd"] = round(general_stats["eliminations"] / general_stats["deaths"], 2)
        else:
            general_stats["kpd"] = None

        # Generate Featured Stats
        for astat in average_stats:
            if astat in general_stats or astat in hero_stats:
                if astat in hero_stats:
                    val = hero_stats[astat]
                else:
                    val = general_stats[astat]
                featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": val})

        if statsIndex == 0:
            data["quickplay"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}
        else:
            data["competitive"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}

    return data
