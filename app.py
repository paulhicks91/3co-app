import re
import os
from datetime import datetime

from flask import Flask, url_for, render_template, request, jsonify, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_compress import Compress

from bigquery import create_bigquery_client, run_query

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

Compress(app)

# browsers that can be parsed from the UA, doesn't include crawlers
BROWSERS = [
    'camino', 'chrome', 'firefox', 'galeon', 'kmeleon', 'konqueror', 'links',
    'lynx', 'msie', 'msn', 'netscape', 'opera', 'safari', 'seamonkey', 'webkit'
]

app.jinja_env.globals['current_year'] = datetime.utcnow().year
app.jinja_env.globals['nav_links'] = [
    {'name': 'Home', 'url': 'main'},
    {'name': 'Queen Beans', 'url': 'queen_beans'},
    {'name': 'Total Set Beans', 'url': 'total_set_beans'},
    {'name': 'Fastest Eco - QP/Ranked', 'url': 'fastest_eco_qp_ranked'},
    {'name': 'Lurk Bot - BETA', 'url': 'lurk'},
]

MAP_IMAGES = [
    'the-black-queens-keep.png',
    'the-helix-temple.png',
    'the-nesting-flats.png',
    'the-pod.png',
    'the-spire.png',
    'the-split-juniper.png',
    'the-tally-fields.png',
    'the-throne-room.png'
]


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
    return render_template('home.jinja2', title='Home')


@app.route('/queen-beans')
def queen_beans():
    bigquery_client = create_bigquery_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/queen_bean_rankings.sql', bigquery_client)
    short_desc = 'Leaderboards for the most queen beans by a single player in a single map'
    desc = 'A Queen Bean is a berry that is knocked in by a queen. VV rare and VV hard to do.<br>' \
           'These are the people with the most queen beans in a single map.<br>' \
           'The stats are only from Quick Play or Ranked and do not include Customs or Locals.'

    for row in query_results:

        map_name = row['map']
        map_image = re.sub('[^a-z0-9 ]+', '', map_name.lower()).replace(' ', '-') + '.png'
        webp = map_image.replace('.png', '.webp')
        player_stats = []
        for player_entry in row['player_stats']:
            player_stats.append({
                'metric': player_entry['totalBerryDeposits'],
                'player': player_entry['nickname'],
                'ts': player_entry['matchTimestamp'].isoformat()
            })

        leaderboard_items.append({
            'content_title': map_name,
            'map_image': url_for('static', filename=f'maps/{map_image}'),
            'webp': url_for('static', filename=f'maps/{webp}'),
            'leaderboard_entries': player_stats
        })

    if request.user_agent.browser in BROWSERS:
        return render_template('solo-leaderboards.jinja2', leaderboard_title='Queen Bean', short_desc=short_desc,
                               desc=desc, leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


@app.route('/fastest-eco-qp-ranked')
def fastest_eco_qp_ranked():
    bigquery_client = create_bigquery_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/ranked_qp_fastest_eco.sql', bigquery_client)
    short_desc = 'Leaderboards for the teams with the fastest economic victories for a single map'
    desc = 'These are the teams with the fastest economic victories for a single map.<br>' \
           'The stats are only from Quick Play or Ranked and do not include Customs or Locals.'

    for row in query_results:

        map_name = row['map']
        map_image = re.sub('[^a-z0-9 ]+', '', map_name.lower()).replace(' ', '-') + '.png'
        webp = map_image.replace('.png', '.webp')
        player_stats = []
        for match_entry in row['match_stats']:
            ind_player_stats = []
            for player_stat in match_entry['player']:
                ind_player_stats.append(
                    {
                        'player': player_stat['nickname'],
                        'individual_metric': '{:d} beans'.format(player_stat['totalBerryDeposits']),
                        'role': player_stat['role']
                    }
                )

            player_stats.append(
                {
                    'metric': '{:.3f}s'.format(match_entry['duration']),
                    'ts': match_entry['matchTimestamp'].isoformat(),
                    'players': ind_player_stats
                }
            )

        leaderboard_items.append(
            {
                'content_title': map_name,
                'map_image': url_for('static', filename=f'maps/{map_image}'),
                'webp': url_for('static', filename=f'maps/{webp}'),
                'leaderboard_entries': player_stats
            }
        )

    if request.user_agent.browser in BROWSERS:
        return render_template('team-leaderboards.jinja2', leaderboard_title='Fastest Eco - QP/Ranked', desc=desc,
                               short_desc=short_desc, leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


@app.route('/lurk', methods=['GET', 'POST'])
def lurk():
    bigquery_client = create_bigquery_client()
    if request.method == 'GET':
        lurk_queue = run_query('bigquery/queries/get_lurk_key.sql', bigquery_client)
        for row in lurk_queue:
            if lurk_key := row['lurk_key']:
                return render_template('lurk.jinja2', lurk_key=lurk_key)
        return render_template('lurk.jinja2', lurk_key='')
    if request.method == 'POST':
        lurk_key = request.form['lurk-key'].upper()
        bigquery_client.query(f'INSERT hot-chee-to.match_stats.lurk_queue (lurk_key) VALUES(\'{lurk_key}\')')
        return redirect(url_for('lurk_active', lurk_key=lurk_key))


@app.route('/lurk/<lurk_key>')
def lurk_active(lurk_key):
    if re.match('^[a-zA-Z]{6}$', lurk_key):
        return render_template('lurking.jinja2', lurk_key=lurk_key.upper())


@app.route('/total-set-beans')
def total_set_beans():
    bigquery_client = create_bigquery_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/ranked_qp_total_set_beans.sql', bigquery_client)
    short_desc = 'Leaderboards for most beans in a single set by a single player'
    desc = 'These are the stats for the most beans by a single player in a single set.<br>' \
           'It is broken out by number of maps in a set (3, 4 or 5) because 32 beans in a 3-map set is much ' \
           'harder to accomplish than 32 beans in a 5-map set.<br>Theoretical max beans are as follows: ' \
           '36 beans for a 3-map set, 47 beans for a 4-map set and 58 for a 5-map set.<br>' \
           'The stats are only from Quick Play or Ranked and do not include Customs or Locals.'

    for i, row in enumerate(query_results):

        n_maps = row['totalMaps']
        map_image = MAP_IMAGES[i]
        webp = map_image.replace('.png', '.webp')
        player_stats = []
        for player_entry in row['player_stats']:
            player_stats.append({
                'metric': player_entry['totalBerryDeposits'],
                'player': player_entry['nickname'],
                'ts': player_entry['matchTimestamp'].isoformat()
            })

        leaderboard_items.append({
            'content_title': f'{n_maps}-Map Set',
            'map_image': url_for('static', filename=f'maps/{map_image}'),
            'webp': url_for('static', filename=f'maps/{webp}'),
            'leaderboard_entries': player_stats
        })

    if request.user_agent.browser in BROWSERS:
        return render_template('solo-leaderboards.jinja2', leaderboard_title='Set Bean Total', desc=desc,
                               metric_class_modifier='-2', short_desc=short_desc, leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
