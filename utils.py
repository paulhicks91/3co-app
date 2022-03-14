import json
from datetime import datetime, timezone
import ntpath
from os import mkdir, walk, listdir, remove
from os.path import isdir, isfile
import pathlib
from os.path import sep as os_sep
from shutil import copy2
from typing import Union, List, Tuple, Set, FrozenSet, MutableSet, AbstractSet, Dict, DefaultDict, OrderedDict, Optional


ListTypeTuple = (List, Tuple, Set, FrozenSet, MutableSet, AbstractSet)
ListStrTypeTuple = (List, Tuple, Set, FrozenSet, MutableSet, AbstractSet, str)
DictTypeTuple = (Dict, DefaultDict, OrderedDict)


def json_load(filename: str, encoding: Optional[str] = 'utf-8'):
    with open(filename, 'r', encoding=encoding) as f:
        json_object = json.load(f)
    f.close()
    return json_object


def convert_bool_to_str(input_value):
    if isinstance(input_value, DictTypeTuple):
        return {key: convert_bool_to_str(value) for key, value in input_value.items()}
    elif isinstance(input_value, bool):
        return str(input_value).upper()
    elif isinstance(input_value, ListTypeTuple):
        return [convert_bool_to_str(value) for value in input_value]

    return input_value


def parse_timestamp(filename: str) -> Union[Tuple[datetime, str], Tuple[datetime, None]]:
    # remove the path from the filename to get only the base filename
    base_filename = ntpath.basename(filename)
    # filename should have
    stripped_timestamp = base_filename.split('-', 1)[-1].split('.')[0]

    try:
        # extract the timestamp from the filename
        filename_timestamp = datetime.fromtimestamp(datetime.strptime(stripped_timestamp, '%Y-%m-%d-%H-%M-%S')
                                                    .timestamp(), tz=timezone.utc)
        # get the time the file was modified from the file metadata
        file_last_modified_timestamp = datetime.fromtimestamp(pathlib.Path(filename).stat().st_mtime, tz=timezone.utc)
        # get the absolute value of the difference between the two timestamps in seconds
        file_timedelta = abs(filename_timestamp - file_last_modified_timestamp).total_seconds()
        # the file metadata can be off by up to 2s, file_last_modified_timestamp should always be in UTC since I think
        # it's in seconds since EPOCH and if the filename time is the same then that means both are UTC
        if file_timedelta < 2.5:
            return filename_timestamp, 'utc'
        # add 2.5 to the timestamp then get the remainder after dividing by 1h in seconds (3600) to see if
        # the offset is almost exactly to the hour then see exactly how many hours it is off
        # if it's between 4 and 10 hours off that means 1 is probably UTC and the other is a US timezone
        # I'll then take the file_last_modified_timestamp because that's the one that's probably UTC
        elif ((file_timedelta + 2.5) % 3600 < 5) and 4 <= (file_timedelta + 2.5) // 3600 <= 10:
            return file_last_modified_timestamp, 'utc'
        else:
            # return the timestamp stripped from the filename and None since we can't determine a timezone
            return file_last_modified_timestamp, None
    except Exception as e:
        print(f'ERROR: {type(e).__name__} Could not parse timestamp from {filename}')
        raise e


def validate_path(filename: str) -> str:
    if isfile(filename):
        return filename
    split_filename = filename.replace('\\', '/').split('/')
    split_len = len(split_filename)
    if split_len > 1:
        filename = ''
        if '.' not in split_filename[-1]:
            path_list = split_filename
        else:
            path_list = split_filename[:-1]
        for dir_name in path_list:
            if dir_name:
                if not filename:
                    filename = dir_name
                else:
                    filename = f'{filename}{os_sep}{dir_name}'
                if not isdir(filename):
                    mkdir(filename)

        return os_sep.join(split_filename)
    else:
        if '.' not in filename:
            if not isdir(filename):
                mkdir(filename)
        return filename


def new_join(path: str, *paths) -> str:
    path = os_sep.join([split_part for split_part in path.replace('\\', '/').split('/') if split_part])
    if not path:
        path = os_sep
    for path_part in paths:
        path_fixed = os_sep.join([split_part for split_part in path_part.replace('\\', '/').split('/') if split_part])
        if path_fixed:
            path = f'{path}{os_sep}{path_fixed}'
    return validate_path(path)


def get_dir_files(file_dir: str = '.', search_children: bool = False):
    file_list = []
    if search_children:
        for root, dirs, files in walk(file_dir):
            for file in files:
                file_list.append(new_join(root, file))
    else:
        for file in listdir(file_dir):
            file_path = new_join(file_dir, file)
            if isfile(file_path):
                file_list.append(new_join(file_dir, file))
    return file_list


def copy_file(old_location: str, new_location: str, overwrite: bool = True):
    if isfile(old_location):
        if isfile(new_location):
            if overwrite:
                remove(new_location)
            else:
                return
        copy2(old_location, new_location)
        return new_location
