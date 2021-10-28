from bigquery import create_client, put_match_stats_from_file_list
from utils import json_load, get_dir_files, copy_file
from ntpath import basename


CONFIGS = json_load('tmp/config.json')


def upload_match_files():
    match_files = [match_file for match_file in get_dir_files(CONFIGS['match_dir']) if match_file.endswith('.json')]
    bq_client = create_client()
    username = CONFIGS.get('username', None)
    if username:
        query = f"""
        SELECT filename FROM `hot-chee-to.match_stats.matchStats` 
        WHERE submittedBy = \'{username}\' GROUP BY filename;
        """
        uploaded_files_query = bq_client.query(query)
        query_results = uploaded_files_query.result()
        previously_uploaded = [row.filename for row in query_results]
        match_files = [file for file in match_files if basename(file) not in previously_uploaded]

    put_match_stats_from_file_list(match_files, bq_client, username)


if __name__ == '__main__':
    upload_match_files()
