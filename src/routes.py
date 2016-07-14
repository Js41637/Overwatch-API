from flask import Blueprint, make_response, request, jsonify, abort
import utils
import parsers

bp = Blueprint("routes", __name__)

@bp.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'ok': False, 'error': 'profile not found'}), 404)

@bp.route('/', methods=['GET'])
def root():
    return "Hello, nufin to see here"

@bp.route('/u/<user>/stats/')
def get_user_stats(user):
    data = utils.find_user(user, request.values.get("region", None))
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_stats(page, region, battletag, 'both')

    return return_data(stats)

@bp.route('/u/<user>/stats/<version>')
def get_user_stats_type(user, version):
    if version == 'quickplay' or version == 'competitive' or version == 'both':
        data = utils.find_user(user, request.values.get("region", None))
    else:
        return jsonify({'ok': False, 'data': 'Invalid Type'})
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_stats(page, region, battletag, version)

    try:
        if stats["error"]:
            return return_error(stats["msg"])
    except:
        return return_data(stats)

@bp.route('/u/<user>/heroes/')
def get_user_heroes(user):
    data = utils.find_user(user, request.values.get("region", None))
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_heroes(page, region, battletag, 'both')

    try:
        if stats["error"]:
            return return_error(stats["msg"])
    except:
        return return_data(stats)

@bp.route('/u/<user>/heroes/<version>')
def get_user_heroes_type(user, version):
    if version == 'quickplay' or version == 'competitive' or version == 'both':
        data = utils.find_user(user, request.values.get("region", None))
    else:
        return jsonify({'ok': False, 'data': 'Invalid Type'})
    if not data:
        abort(404)

    page, region, battletag = data[0]
    stats = parsers.parse_heroes(page, region, battletag, version)

    try:
        if stats["error"]:
            return return_error(stats["msg"])
    except:
        return return_data(stats)

def return_data(data):
    return jsonify({'ok': True, 'data': data})

def return_error(data):
        return jsonify({'ok': False, 'error': data})
