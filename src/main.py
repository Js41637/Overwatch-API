from flask import Flask, render_template, jsonify, make_response
import routes

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template("index.html")

app.register_blueprint(routes.bp, url_prefix='/api')

@app.errorhandler(404)
def page_not_found(e):
    return make_response(jsonify({
        'ok': False,
        'error': 'Sorry, nothing at this URL.'
    }), 404)

@app.errorhandler(500)
def application_error(e):
    return make_response(jsonify({
        'ok': False,
        'error': 'shits_fucked',
        'message': '{}'.format(e),
        'please': 'report this, thanks'
    }), 500)

if __name__ == '__main__':
    app.run(debug=True, host='localhost')
