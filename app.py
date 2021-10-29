import re
import os
from datetime import datetime

from flask import Flask, url_for, render_template, redirect, request, jsonify
from werkzeug.contrib.fixers import ProxyFix

from bigquery import create_client, run_query


app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

# browsers that can be parsed from the UA, doesn't include crawlers
BROWSERS = [
    'camino', 'chrome', 'firefox', 'galeon', 'kmeleon', 'konqueror', 'links',
    'lynx', 'msie', 'msn', 'netscape', 'opera', 'safari', 'seamonkey', 'webkit'
]

app.jinja_env.globals['current_year'] = datetime.utcnow().year


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('/favicon.ico')


@app.route('/favicon.svg')
def favicon_svg():
    return app.send_static_file('/favicon.svg')


@app.route('/favicon.png')
def favicon_png():
    return app.send_static_file('/favicon.png')


@app.route('/')
def main():
    """
    redirects to /queen_beans
    """
    return redirect(url_for('queen_beans'))


@app.route('/queen-beans')
def queen_beans():
    bigquery_client = create_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/queen_bean_rankings.sql', bigquery_client)

    for row in query_results:

        map_name = row['map']
        map_image = re.sub('[^a-z0-9 ]+', '', map_name.lower()).replace(' ', '-') + '.png'
        player_stats = []
        for player_entry in row['player_stats']:

            player_stats.append({
                'metric': player_entry['totalBerryDeposits'],
                'player': player_entry['nickname'],
                'ts': player_entry['matchTimestamp'].isoformat()
            })

        leaderboard_items.append({
            'map_name': map_name,
            'map_image': url_for('static', filename=f'maps/{map_image}'),
            'leaderboard_entries': player_stats
        })

    if request.user_agent.browser in BROWSERS:
        return render_template('solo-leaderboards.jinja2', leaderboard_title='Queen Bean', metric_type='beans',
                               leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
