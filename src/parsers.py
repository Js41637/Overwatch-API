from lxml import etree
import utils
import ranks

def parse_stats(page, region, battletag):
    parsed = etree.HTML(page)

    data = {"player": {}, "stats": { "quickplay": {}, "competitive": {}}}

    data["player"]["battletag"] = battletag
    data["player"]["region"] = region
    data["player"]["level"] = int(parsed.find(".//div[@class='player-level']/div").text)
    data["player"]["rank"] = None # Soon

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
        for key, val in ranks.data.items():
            if key in bg_image:
                data["player"]["rank"] = val
                break
        else:
            data["player"]["rank"] = None

    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='0x02E00000FFFFFFFF']")

    #Stats contains both Quick and Comp, if no comp, set it to Null
    if len(stats) != 2:
        data["stats"]["competitive"] = None

    # Go through both QuickPlay and Competetive stats
    for i, item in enumerate(stats):
        stat_groups = item

        overall_stats = {}
        game_stats = {}
        featured_stats = []

        death_box = stat_groups[4]
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
        #Manually add KPD
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

def parse_heroes(page, region, battletag):
    parsed = etree.HTML(page)

    data = {"quickplay": {}, "competitive": {}}

    stats = parsed.xpath(".//div[@data-category-id='overwatch.guid.0x0860000000000021']")

    for i, item in enumerate(stats):
        built_heroes = []
        nostats = False
        heroes = item.xpath(".//div[@class='bar-text']")
        for ii, hero in enumerate(heroes):
            htime = hero.find(".//div[@class='description']").text
            # If the first hero has no playtime then we can assume that none have been played
            # and that they haven't played comp mode so we will ignore all the rest
            if htime == '--':
                if nostats:
                    continue
                elif ii == 0 and i == 1:
                    nostats = True
                    continue
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
