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
    data = utils.get_data(user, request.values.get("region", None), platform)
    if not data:
        abort(404)

    return return_data({"player": data["player"]})

@bp.route('/u/<user>/blob')
@bp.route('/u/<user>/blob/')
def get_user_blob(user):
    platform = request.values.get("platform", "pc")
    data = utils.get_data(user, request.values.get("region", None), platform)
    if not data:
        abort(404)

    return return_data(data)

@bp.route('/u/<user>/stats')
@bp.route('/u/<user>/stats/')
@bp.route('/u/<user>/stats/<version>')
def get_user_stats(user, version='both'):
    platform = request.values.get("platform", "pc")
    data = utils.get_data(user, request.values.get("region", None), platform)
    if not data:
        abort(404)

    del data["stats"]["heroes"]
    if version == 'quickplay':
         del data["stats"]["competitive"]
    if version == 'competitive':
        del data["stats"]["quickplay"]

    return return_data(data)

@bp.route('/u/<user>/heroes')
@bp.route('/u/<user>/heroes/')
@bp.route('/u/<user>/heroes/<version>')
def get_user_heroes(user, version='both'):
    platform = request.values.get("platform", "pc")
    data = utils.get_data(user, request.values.get("region", None), platform)
    if not data:
        abort(404)

    out = {
        "quickplay": data["stats"]["quickplay"]["playtimes"],
        "competitive": data["stats"]["competitive"]["playtimes"]
    }
    if version == 'quickplay':
         del out["competitive"]
    if version == 'competitive':
        del out["quickplay"]

    return return_data(out)

@bp.route('/u/<user>/hero')
@bp.route('/u/<user>/hero/')
@bp.route('/u/<user>/hero/<hero>')
@bp.route('/u/<user>/hero/<hero>/')
@bp.route('/u/<user>/hero/<hero>/<version>')
def get_user_hero(user, hero=None, version='both'):
    if hero is None:
        return return_error("No hero specified")
    heroname = hero.lower()
    if heroname not in datastore.heroes:
        return return_error("Invalid hero")
    if version != 'quickplay' and version != 'competitive' and version != 'both':
        return return_error('Invalid Type')

    platform = request.values.get("platform", "pc")
    data = utils.get_data(user, request.values.get("region", None), platform)
    if not data:
        abort(404)

    if version == 'quickplay':
         del data["stats"]["heroes"][heroname]["stats"]["competitive"]
    if version == 'competitive':
        del data["stats"]["heroes"][heroname]["stats"]["quickplay"]

    return return_data(data["stats"]["heroes"][heroname])


def return_data(data):
    return jsonify({'ok': True, 'data': data})


def return_error(data):
    return jsonify({'ok': False, 'error': data})
