from lxml import etree
import utils
import datastore

def parse_stats(page, region, battletag, version):
    if version == 'both':
        data = {"player": {}, "stats": { "quickplay": {}, "competitive": {}}}
    elif version == 'quickplay':
        data = {"player": {}, "stats": { "quickplay": {}}}
    elif version == 'competitive':
        data = {"player": {}, "stats": { "competitive": {}}}

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

    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='0x02E00000FFFFFFFF']")

    #Stats contains both Quick and Comp, if no comp, set it to Null
    if len(stats) != 2:
        if version == 'competitive':
            return {"error": True, "msg": "No competitive stats"}
        elif version == 'both':
            data["stats"]["competitive"] = None

    # Go through both QuickPlay and Competetive stats
    for i, item in enumerate(stats):
        if version == 'competitive' and i == 0:
            continue
        elif version == 'quickplay' and i == 1:
            continue

        stat_groups = item

        overall_stats = {}
        game_stats = {}
        featured_stats = []

        game_box = stat_groups[6]

        # Fetch Overall stats
        wins = int(game_box.xpath(".//text()[. = 'Games Won']/../..")[0][1].text.replace(",", ""))
        g = game_box.xpath(".//text()[. = 'Games Played']/../..")
        games = int(g[0][1].text.replace(",", ""))

        overall_stats["wins"] = wins
        overall_stats["win_rate"] = round(((float(wins) / games) * 100), 1)
        overall_stats["losses"] = games - wins
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

        # Featured Stats
        for astat in average_stats:
            if average_stats[astat] != 0:
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
        if version == 'competitive' and i == 0:
            continue
        elif version == 'quickplay' and i == 1:
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

    heroid = datastore.heroes[hero]

    parsed = etree.HTML(page)
    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='{0}']".format(heroid))

    #Stats contains both Quick and Comp, if no comp, set it to Null
    if len(stats) != 2:
        if version == 'competitive':
            return {"error": True, "msg": "No competitive stats"}
        elif version == 'both':
            data["competitive"] = None

    # Go through both QuickPlay and Competetive stats
    for i, item in enumerate(stats):
        if version == 'competitive' and i == 0:
            continue
        elif version == 'quickplay' and i == 1:
            continue

        hero_stats = {}
        general_stats = {}
        featured_stats = []
        overall_stats = {}

        stat_groups = item
        hero_box = stat_groups[0]
        game_box = stat_groups[7]

        # Fetch Overall stats
        wins = int(game_box.xpath(".//text()[. = 'Games Won']/../..")[0][1].text.replace(",", ""))
        g = game_box.xpath(".//text()[. = 'Games Played']/../..")
        games = int(g[0][1].text.replace(",", ""))

        overall_stats["wins"] = wins
        overall_stats["win_rate"] = round(((float(wins) / games) * 100), 1)
        overall_stats["losses"] = games - wins
        overall_stats["games"] = games

        # Fetch Game Stats
        average_stats = {}
        for hstat in hero_box.findall(".//tbody/tr"):
            name, value = hstat[0].text.lower().replace(" ", "_").replace("_-_", "_"), hstat[1].text
            amount = utils.parseInt(value)
            if 'average' in name.lower():
                # Don't include average stats in the general_stats, use them for the featured stats section
                average_stats[name.replace("_average", "")] = amount
            else:
                hero_stats[name] = amount

        for subbox in stat_groups[1:]:
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
        general_stats["kpd"] = round(general_stats["eliminations"] / general_stats["deaths"], 2)

        # Featured Stats
        for astat in average_stats:
            if average_stats[astat] != 0:
                if astat in hero_stats:
                    val = hero_stats[astat]
                else:
                    val = general_stats[astat]
                featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": val})

        if i == 0:
            data["quickplay"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}
        else:
            data["competitive"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}

    return data
