from lxml import etree
import utils
import datastore

def parse_stats(page, region, battletag, platform):
    data = {}
    parsed = etree.HTML(page)

    data["player"] = parse_user_data(parsed, region, battletag, platform)
    data["stats"] = parse_game_stats(parsed)
    data["stats"]["heroes"] = parse_hero(parsed)

    playtimeData = parse_heroes(parsed)
    data["stats"]["quickplay"]["playtimes"] = playtimeData["quickplay"]
    data["stats"]["competitive"]["playtimes"] = playtimeData["competitive"]

    return data

def parse_user_data(parsed, region, battletag, platform):
    player = {}
    mast_head = parsed.xpath(".//div[@class='masthead-player']")[0]

    player["battletag"] = battletag
    player["region"] = region if platform == 'pc' else None
    player["platform"] = platform
    player["level"] = int(mast_head.find(".//div[@class='player-level']/div").text)
    player["avatar"] = mast_head.find(".//img[@class='player-portrait']").attrib['src']

    # Try and fetch Comp Rank, Comp Teir and Comp Teir Image
    comp_tree = mast_head.find(".//div[@class='competitive-rank']")
    if comp_tree is not None:
        comprank = comp_tree.find(".//div")
        compimg = comp_tree.find(".//img")
        if compimg is not None:
            imgsrc = compimg.get('src')
            player["compteirimage"] = imgsrc
            imagename = imgsrc.split('/')[-1]
            for key, val in datastore.comp_ranks.items():
                if key in imagename:
                    player["compteir"] = val
                    break
            else:
                player["compteir"] = None
        else:
            player.update({ 'compteir': None, 'compteirimg': None })
        player["comprank"] = int(comprank.text) if comprank is not None else None
    else:
        player.update({ 'comprank': None, 'compteir': None, 'compteirimg': None })

    # Try and fetch Rank
    rank = mast_head.xpath(".//div[@class='player-level']")[0]
    try:
        bg_image = [x for x in rank.values() if 'background-image' in x][0]
    except IndexError:
        player["rank"] = 0
    else:
        for key, val in datastore.ranks.items():
            if key in bg_image:
                player["rank"] = val
                break
        else:
            player["rank"] = None

    return player

# Go through both QuickPlay and Competetive stats
def parse_game_stats(parsed):
    # Start with them filled in so if there is no stats for some reason, it keeps the empty objects and stuff
    data = {"quickplay": {"overall_stats": {}, "game_stats": {}, "featured_stats": []}, "competitive": {"overall_stats": {}, "game_stats": {}, "featured_stats": []}}
    stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='0x02E00000FFFFFFFF']")

    if len(stats) == 1:
        data["competitive"]["is_empty"] = True

    for i, item in enumerate(stats):
        overall_stats, game_stats, average_stats, featured_stats = {}, {}, {}, []

        # Fetch Game Stats
        for subbox in item:
            stats = subbox.findall(".//tbody/tr")
            for stat in stats:
                name, value = stat[0].text.lower().replace(" ", "_").replace("_-_", "_"), stat[1].text
                amount = utils.parse_int(value, False)
                if 'average' in name.lower():
                    # Don't include average stats in the game_stats, use them for the featured stats section
                    average_stats[name.replace("_average", "")] = amount
                else:
                    game_stats[name] = amount

        # Manually add KPD
        if 'eliminations' in game_stats and 'deaths' in game_stats:
            game_stats["kpd"] = round(game_stats["eliminations"] / game_stats["deaths"], 2)
        else:
            general_stats["kpd"] = None

        overall_stats = parse_overall_stats(game_stats, average_stats)

        # Generate Featured Stats
        for astat in average_stats:
            if average_stats[astat] != 0:
                if astat[:-1] in game_stats:
                    featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": game_stats[astat[:-1]]})
                else:
                    featured_stats.append({ "name": astat.replace("_", " "), "avg": average_stats[astat], "value": game_stats[astat]})

        if i == 0:
            data["quickplay"] = {"featured_stats": featured_stats, "game_stats": game_stats, "overall_stats": overall_stats}
        else:
            data["competitive"] = {"featured_stats": featured_stats, "game_stats": game_stats, "overall_stats": overall_stats}

    return data

# Get playtime each hero for Quickplay and Competitive
def parse_heroes(parsed):
    playtimes = { 'quickplay': [], 'competitive': [] }
    playtimestats = parsed.xpath(".//div[@data-category-id='overwatch.guid.0x0860000000000021']")
    for i, item in enumerate(playtimestats):
        built_heroes = []
        heroes = item.xpath(".//div[@class='bar-text']")
        for ii, hero in enumerate(heroes):
            htime = hero.find(".//div[@class='description']").text
            # If the first hero has no playtime then we can assume that none have been played
            # and that they haven't played comp mode so we will ignore all the rest
            if htime == '--':
                if ii == 0 and i == 1:
                    break
                else:
                    htime = '0'
            hname = hero.find(".//div[@class='title']").text
            cname = hname.replace(".", "").replace(": ", "").replace(u"\xfa", "u").replace(u'\xf6', 'o')
            time = utils.parse_int(htime, False)

            built_heroes.append({ 'name': hname, 'time': time, 'extended': '/hero/' + cname.lower() })

        if i == 0:
            playtimes['quickplay'] = built_heroes
        else:
            playtimes['competitive'] = built_heroes

    return playtimes

# Get individual hero data for every hero and their Quickplay and Competitive stats
def parse_hero(parsed):
    heroes = {}
    for key, hero in datastore.heroes.items():
        stats = parsed.xpath(".//div[@data-group-id='stats' and @data-category-id='{0}']".format(hero["id"]))
        heroes[key] = {
            "name": hero["name"],
            "class": hero["class"],
            "stats": {"quickplay": {"featured_stats": [], "general_stats": {}, "overall_stats": {}, "hero_stats": {}}, "competitive": {"featured_stats": [], "general_stats": {}, "overall_stats": {}, "hero_stats": {}}}
        }

        if len(stats) == 0:
            heroes[key]["stats"]["quickplay"]["is_empty"] = True
            heroes[key]["stats"]["competitive"]["is_empty"] = True
            continue

        if len(stats) == 1:
            heroes[key]["stats"]["competitive"]["is_empty"] = True

        # Go through both QuickPlay and Competetive stats
        for statsIndex, item in enumerate(stats):
            hero_stats, general_stats, overall_stats, average_stats, featured_stats = {}, {}, {}, {}, []

            hbtitle = item[0].find(".//span[@class='stat-title']").text
            if hbtitle == 'Hero Specific':
                hero_box = item[0]
                startingPos = 1
            else:
                hero_box = None
                startingPos = 0

            # Fetch Hero Specific Stats
            if hero_box is not None:
                for hstat in hero_box.findall(".//tbody/tr"):
                    name, value = hstat[0].text.lower().replace(" ", "_").replace("_-_", "_"), hstat[1].text
                    amount = utils.parse_int(value, False)
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
                    amount = utils.parse_int(value, False)
                    if 'average' in name.lower():
                        # Don't include average stats in the general_stats, use them for the featured stats section
                        average_stats[name.replace("_average", "")] = amount
                    else:
                        general_stats[name] = amount

            overall_stats = parse_overall_stats(general_stats, average_stats)

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
                heroes[key]["stats"]["quickplay"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}
            else:
                heroes[key]["stats"]["competitive"] = {"featured_stats": featured_stats, "general_stats": general_stats, "overall_stats": overall_stats, "hero_stats": hero_stats}

    return heroes

def parse_overall_stats(stats, averages):
    wins = stats['games_won'] if 'games_won' in stats else 0
    games = stats['games_played'] if 'games_played' in stats else None
    losses = stats['games_lost'] if 'games_lost' in stats else None
    ties = stats['games_tied'] if 'games_tied' in stats else None

    if games is None:
        elim_done = stats['eliminations'] if 'eliminations' in stats else None
        avg_elim = averages['eliminations'] if 'eliminations' in averages else None

        if (elim_done and avg_elim):
            games = int(elim_done // avg_elim)
            losses = games - wins

    # If there is no games we can assume they haven't finished any games as this hero
    if games is not None:
        winrate = round((float(wins) / games), 1) if int(wins) is not 0 else 0
        losses = losses if losses else 0
        ties = ties if ties else 0
    else:
        winrate = None
        wins = None if wins == 0 else wins

    return { 'wins': wins, 'win_rate': winrate, 'losses': losses, 'games': games, 'ties': ties }
