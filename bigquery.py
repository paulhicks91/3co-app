from google.cloud import bigquery, pubsub_v1
import os
from datetime import datetime
import ntpath
from utils import json_load, parse_timestamp, convert_bool_to_str
import uuid
from json import dumps
import io


PROJECT_NAME = 'hot-chee-to'
DATASET = 'match_stats'
DEFAULT_SCHEMA_FILE = 'bigquery/schema.json'
# optional service account file for running locally
SERVICE_ACCOUNT_JSON = 'bigquery/service-account.json'


def create_pubsub_client(service_account_json_filename: str = SERVICE_ACCOUNT_JSON, publisher: bool = True):
    if not os.path.isfile(service_account_json_filename):
        if publisher:
            return pubsub_v1.PublisherClient()
        return pubsub_v1.SubscriberClient()
    else:
        if publisher:
            return pubsub_v1.PublisherClient.from_service_account_json(service_account_json_filename)
        return pubsub_v1.SubscriberClient.from_service_account_json(service_account_json_filename)


def create_bigquery_client(service_account_json_filename: str = SERVICE_ACCOUNT_JSON) -> bigquery.Client:
    if not os.path.isfile(service_account_json_filename):
        print(f'file {service_account_json_filename} does not exist {os.getcwd()}')
        return bigquery.Client()
    return bigquery.Client.from_service_account_json(service_account_json_filename)


def create_schema_from_json(schema_json_list: list):
    schema = []
    schema_json_list = sorted(schema_json_list, key=lambda field: field['name'])
    for schema_field in schema_json_list:
        field_name = schema_field.get('name', None)
        field_mode = schema_field.get('mode', 'NULLABLE')
        field_type = schema_field.get('type', None)
        field_fields = schema_field.get('fields', [])
        if not (field_name and field_type):
            raise ValueError(f'either field name or field type not specified field_name: {field_name} field_type: '
                             f'{field_type} full field dict: {schema_field}')
        if field_fields:
            field_fields = create_schema_from_json(field_fields)

        schema.append(bigquery.SchemaField(field_name, field_type, field_mode, fields=field_fields))

    return schema


def validate_format_match_json(match_stats_filename: str, username: str = None):
    parsed_filename = ntpath.basename(match_stats_filename)

    timestamp, time_zone = parse_timestamp(match_stats_filename)
    print(f'Loading stats from {parsed_filename}')
    match_stats = json_load(match_stats_filename)

    validated_time_zone = False
    if isinstance(time_zone, str) and time_zone.lower() == 'utc':
        validated_time_zone = True

    data = {
        'createdTimestamp': datetime.utcnow().isoformat(),
        'id': str(uuid.uuid4()),
        'filename': parsed_filename,
        'matchTimestamp': timestamp.isoformat(),
        'timestampValidated': validated_time_zone,
        'submittedBy': username
    }

    match_stats.update(data)

    games = match_stats.get('games')
    maps = match_stats.get('mapPool')

    if len(games) <= len(maps):
        n_games = len(games)

        for i, game_map in enumerate(maps):
            if i == n_games:
                break
            game = games[i]
            game['gameMap'] = game_map
            games[i] = game

    match_stats['games'] = games

    match_stats = convert_bool_to_str(match_stats)
    return dumps(match_stats, separators=(',', ':'), sort_keys=True)


def put_match_stats_from_file_list(match_file_list: list, bigquery_client: bigquery.Client, username: str = None,
                                   schema_filename: str = DEFAULT_SCHEMA_FILE):
    if not match_file_list:
        print('Empty list passed to function, please attach a list containing 1+ filenames')
        return

    match_files = sorted(match_file_list)
    n_match_files = len(match_files)
    print(f'Validating and formatting {n_match_files} files')
    formatted_match_list = []
    for match in match_files:
        try:
            formatted_match = validate_format_match_json(match, username)
            formatted_match_list.append(formatted_match)
        except Exception as e:
            print(f'ERROR: {type(e).__name__} issue processing {ntpath.basename(match)}')
            raise e

    if formatted_match_list:
        print(f'Attempting to upload {len(formatted_match_list)} files to BigQuery DB')
        schema = create_schema_from_json(json_load(schema_filename))
        job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, schema=schema)
        match_fo = io.StringIO('\n'.join(formatted_match_list))
        bigquery_client.load_table_from_file(match_fo, f'{PROJECT_NAME}.{DATASET}.matchStats', job_config=job_config)
        print(f'Uploaded {len(formatted_match_list)} out of {n_match_files} files to BigQuery DB')
    else:
        print(f'Uploaded 0 out of {n_match_files} files to BigQuery DB')


def put_match_stats(match_stats_filename: str, bigquery_client: bigquery.Client, username: str = None,
                    schema_filename: str = DEFAULT_SCHEMA_FILE):
    formatted_stats = validate_format_match_json(match_stats_filename, username)

    schema = create_schema_from_json(json_load(schema_filename))

    job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, schema=schema)
    match_json_fo = io.StringIO(formatted_stats)
    bigquery_client.load_table_from_file(match_json_fo, f'{PROJECT_NAME}.{DATASET}.matchStats', job_config=job_config)
    print(f'Successfully uploaded {ntpath.basename(match_stats_filename)} to BigQuery DB')

    return formatted_stats


def run_query(query_filename: str, bigquery_client: bigquery.Client) -> bigquery.QueryJob:
    print(f'attempting to run {query_filename}')
    with open(query_filename, 'r', encoding='utf-8') as f:
        query = f.read()
    f.close()

    return bigquery_client.query(query)
