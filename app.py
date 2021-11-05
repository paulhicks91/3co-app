import re
import os
from datetime import datetime

from flask import Flask, url_for, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from bigquery import create_client, run_query

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

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
    bigquery_client = create_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/queen_bean_rankings.sql', bigquery_client)

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
        return render_template('solo-leaderboards.jinja2', leaderboard_title='Queen Bean',
                               leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


@app.route('/fastest-eco-qp-ranked')
def fastest_eco_qp_ranked():
    bigquery_client = create_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/ranked_qp_fastest_eco.sql', bigquery_client)

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
        return render_template('team-leaderboards.jinja2', leaderboard_title='Fastest Eco - QP/Ranked',
                               leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


@app.route('/total-set-beans')
def total_set_beans():
    bigquery_client = create_client()
    leaderboard_items = []
    query_results = run_query('bigquery/queries/ranked_qp_total_set_beans.sql', bigquery_client)

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
        return render_template('solo-leaderboards.jinja2', leaderboard_title='Set Bean Total',
                               metric_class_modifier='-2', leaderboard_items=leaderboard_items)
    else:
        return jsonify(leaderboard_items)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
