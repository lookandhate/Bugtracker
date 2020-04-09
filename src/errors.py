from main_app import app
from flask import render_template



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def access_restricted(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(422)
def unprocessable_entity(error):
    return render_template('errors/422.html'), 422
