from flask import Blueprint, make_response, request, jsonify, abort
import utils
import parsers
import cache
import datastore

bp = Blueprint("routes", __name__)


@bp.errorhandler(404)
def not_found(error):
    return make_response(return_error('profile not found'), 404)


@bp.route('/', methods=['GET'])
def root():
    return "Hello, nufin to see here"

@bp.route('/u/<user>')
@bp.route('/u/<user>/')
def get_user(user):
    platform = request.values.get("platform", "pc")
    data = utils.find_user(user, request.values.get("region", None), platform, '', 'info')
    if not data:
        abort(404)

    if data[1] is not None:
        return return_data(data[1])

    page, region, battletag = data[0]
    stats = parsers.parse_stats('basic', page, region, battletag, platform, None)

    cache.set(user + region + platform + 'info', stats, 1200)
    return return_data(stats)

@bp.route('/u/<user>/stats')
@bp.route('/u/<user>/stats/')
@bp.route('/u/<user>/stats/<version>')
def get_user_stats(user, version='both'):
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    platform = request.values.get("platform", "pc")
    data = utils.find_user(user, request.values.get("region", None), platform, version, 'stats')
    if not data:
        abort(404)

    if data[1] is not None:
        return return_data(data[1])

    page, region, battletag = data[0]
    stats = parsers.parse_stats('full', page, region, battletag, platform, version)

    if 'error' in stats and stats['error']:
        return return_error(stats['msg'])
    else:
        cache.set(user + region + platform + version + 'stats', stats, 1200)
        return return_data(stats)


@bp.route('/u/<user>/heroes')
@bp.route('/u/<user>/heroes/')
@bp.route('/u/<user>/heroes/<version>')
def get_user_heroes(user, version='both'):
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    platform = request.values.get("platform", "pc")
    data = utils.find_user(user, request.values.get("region", None), platform, version, 'heroes')
    if not data:
        abort(404)

    if data[1] is not None:
        return return_data(data[1])

    page, region, battletag = data[0]
    stats = parsers.parse_heroes(page, region, battletag, version)

    if 'error' in stats and stats['error']:
        return return_error(stats['msg'])
    else:
        cache.set(user + region + platform + version + 'heroes', stats, 1200)
        return return_data(stats)


@bp.route('/u/<user>/hero')
@bp.route('/u/<user>/hero/')
@bp.route('/u/<user>/hero/<hero>')
@bp.route('/u/<user>/hero/<hero>/')
@bp.route('/u/<user>/hero/<hero>/<version>')
def get_user_hero(user, hero=None, version='both'):
    if hero is None:
        return return_error("No hero specified")
    if hero.lower() not in datastore.heroes:
        return return_error("Invalid hero")
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    platform = request.values.get("platform", "pc")
    data = utils.find_user(user, request.values.get("region", None), platform, version, hero.lower() + 'hero')
    if not data:
        abort(404)

    if data[1] is not None:
        return return_data(data[1])

    page, region, battletag = data[0]
    stats = parsers.parse_hero(page, region, battletag, hero.lower(), version)

    if 'error' in stats and stats['error']:
        return return_error(stats['msg'])
    else:
        cache.set(user + region + platform + version + hero.lower() + 'hero', stats, 1200)
        return return_data(stats)


def return_data(data):
    return jsonify({'ok': True, 'data': data})


def return_error(data):
    return jsonify({'ok': False, 'error': data})
