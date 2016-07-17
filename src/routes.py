from flask import Blueprint, make_response, request, jsonify, abort
import utils
import parsers
import cache

bp = Blueprint("routes", __name__)

@bp.errorhandler(404)
def not_found(error):
    return make_response(return_error('profile not found'), 404)

@bp.route('/', methods=['GET'])
def root():
    return "Hello, nufin to see here"

@bp.route('/u/<user>/stats/')
@bp.route('/u/<user>/stats/<version>')
def get_user_stats(user, version = 'both'):
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    cached = cache.get(user + version)
    if cached is not None:
        return return_data(cached)

    data = utils.find_user(user, request.values.get("region", None))
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_stats(page, region, battletag, version)

    cache.set(user + version, stats, 600)

    try:
        if stats["error"]:
            return return_error(stats["msg"])
    except:
        return return_data(stats)

@bp.route('/u/<user>/heroes/')
@bp.route('/u/<user>/heroes/<version>')
def get_user_heroes(user, version = 'both'):
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    cached = cache.get(user + version)
    if cached is not None:
        return return_data(cached)

    data = utils.find_user(user, request.values.get("region", None))
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_heroes(page, region, battletag, version)

    cache.set(user + version, stats, 600)

    try:
        if stats["error"]:
            return return_error(stats["msg"])
    except:
        return return_data(stats)

def return_data(data):
    return jsonify({'ok': True, 'data': data})

def return_error(data):
        return jsonify({'ok': False, 'error': data})
