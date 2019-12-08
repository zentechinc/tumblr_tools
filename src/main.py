import hashlib
import html
import json
import os
import time
from datetime import datetime
from urllib import parse, request

import pytumblr
from bs4 import BeautifulSoup

from src.config import *


def cleanse_newlines(str):
    return (str.replace('\n', '\\n')).replace('\r', '\\r')


def unescape_html_body(html_body):
    return html.unescape(html_body)


def build_binary_local_name(reduced_like, middlefix='', binary_url=''):
    if reduced_like['like_type'] == 'audio':
        remote_file = request.urlopen(binary_url)
        remote_file.close()
        return remote_file.url[remote_file.url.rfind("/") + 1:]

    prefix = reduced_like['liked_url_hash']
    return '{}_{}{}'.format(prefix, middlefix, get_file_extension_from_name(reduce_url_file_name(binary_url)))


def remove_dirs_from_dir_listing(object_list):
    project_path = os.path.abspath(os.path.dirname(__file__))
    new_list = [target_object for target_object in object_list if
                not os.path.isdir(os.path.join(project_path, target_object))]
    return new_list


def remove_non_dirs_from_dir_listing(object_list):
    project_path = os.path.abspath(os.path.dirname(__file__))
    new_list = [target_object for target_object in object_list if
                os.path.isdir(os.path.join(project_path, target_object))]
    return new_list


def check_if_already_captured(proposed_local_file, list_of_local_files):
    return proposed_local_file in list_of_local_files


def focus_list(object_list, focus_criteria='follows'):
    new_list = list()

    if focus_criteria == 'follows':
        list_to_include = ['follow']
    elif focus_criteria == 'likes':
        list_to_include = ['like']
    else:
        list_to_include = ['post']

    for object_in_list in object_list:
        for search_term in list_to_include:
            if search_term in object_in_list:
                new_list.append(object_in_list)

    return new_list


def get_file_extension_from_name(file_name):
    return file_name[-4:]


def get_dir_list_less_dirs(dir_to_list):
    return remove_dirs_from_dir_listing(os.listdir(dir_to_list))


def focus_photos_on_original(list_of_photos_from_like):
    return [original_binary['original_size']['url'] for original_binary in list_of_photos_from_like]


def focus_player_audio(player_iframe):
    soup = BeautifulSoup(player_iframe, 'html.parser')
    src_parse = soup.select('iframe')
    player_iframe_parse = [i['src'] for i in src_parse if i['src']]
    query_string = parse.urlparse(player_iframe_parse[0])
    audio_url_encoded = query_string.query.split('=')[1]
    return [parse.unquote(audio_url_encoded)]


def focus_vine_video(reduced_like_payload_entry):
    return reduced_like_payload_entry[:reduced_like_payload_entry.rfind('.jpg')]


def get_capture_list_from_like(like, like_type):
    capture_list = []

    if like_type == 'answer':
        pass
    elif like_type == 'audio':
        capture_list = focus_player_audio(like['player'])
    elif like_type == 'photo':
        capture_list = focus_photos_on_original(like['photos'])
    elif like_type == 'text':
        capture_list = get_list_of_binaries_from_html(like['body'])
    elif like_type == 'video_vine':
        capture_list = [like['thumbnail_url']]
    elif like_type == 'video_flickr':
        # print('flickr video')
        # print(like)
        pass
    elif like_type == 'video':
        capture_list = [like['video_url']]

    return capture_list


def get_list_of_binaries_from_html(html_body):
    soup = BeautifulSoup(html_body, 'html.parser')
    img = soup.select('img')
    return [i['src'] for i in img if i['src']]


def get_like_type(like):
    if like['type'] == 'answer':
        return 'answer'

    if like['type'] == 'audio':
        return 'audio'

    if like['type'] == 'photo':
        return 'photo'

    if like['type'] == 'text':
        return 'text'

    if like['type'] == 'video' and like['video_type'] == 'vine':
        return 'video_vine'

    if like['type'] == 'video' and like['video_type'] == 'flickr':
        return 'video_flickr'

    if like['type'] == 'video':
        print('---------> Like Type: Generic Video')
        print('----->:', )
        print(like)
        return 'video'

    return


def smart_capture(reduced_like, known_files):
    # if reduced_like['like_type'] == 'video_vine':
    #     print('enter debug')

    print('----->reduce_like[]:', reduced_like['like_type'])

    if reduced_like['like_type'] in ['audio', 'photo', 'text', 'video']:
        i = 1
        for binary_url in reduced_like['payload']:
            binary_local_name = build_binary_local_name(reduced_like, i, binary_url)
            if not check_if_already_captured(binary_local_name, known_files):
                try:
                    request.urlretrieve(binary_url, os.path.join(reduced_like['path_to_captures'], binary_local_name))
                except request.URLError as e:
                    print('error on capture: {}'.format(binary_url))
                    print('\terror: {}'.format(e))

            i += 1

    if reduced_like['like_type'] == 'video_vine':
        i = 1
        for vine_thumbnail in reduced_like['payload']:
            binary_url = focus_vine_video(vine_thumbnail)
            binary_local_name = build_binary_local_name(reduced_like, i, binary_url)
            if not check_if_already_captured(binary_local_name, known_files):
                try:
                    request.urlretrieve(binary_url, os.path.join(reduced_like['path_to_captures'], binary_local_name))
                except request.URLError as e:
                    print('error on capture: {}'.format(binary_url))
                    print('\terror: {}'.format(e))

            i += 1


def get_liked_url_hash(like):
    return hashlib.md5(like['post_url'].encode('utf-8')).hexdigest()


def get_post_keys(post_to_focus):
    likeable_keys = {'id': post_to_focus['id'], 'reblog_key': post_to_focus['reblog_key']}
    return likeable_keys


def get_blog_keys(tumblr_blog):
    # not currently used
    if type(tumblr_blog) is dict:
        if 'url' in tumblr_blog:
            return {'reduced_url': reduce_blog_url(tumblr_blog['url'])}

    else:
        print('bad blog format recieved: {}'.format(tumblr_blog))
        print('exiting')
        exit()


def fetch_tumblr_client():
    aws_secrets = json.loads(get_secret())
    return pytumblr.TumblrRestClient(
        aws_secrets['consumer_key'],
        aws_secrets['consumer_secret'],
        aws_secrets['oauth_token'],
        aws_secrets['oauth_secret'])


def test_client_api_calls(runtime_options, continuous_run=False, escape_check=False):
    tumblr_response = runtime_options['tumblr_client'].info()

    if 'errors' in tumblr_response:
        if escape_check:
            return False

        if continuous_run:
            go_to_sleeeeeeep()
        else:
            print(tumblr_response)
            print('API calls exhausted for your account, try again in 24 hours')
            exit()

    else:
        config_dictionary['tumblr_call_tracker'] = 0
        return True

    return True


def throttle_call(tumblr_response):
    if 'response' in tumblr_response:
        go_to_sleeeeeeep(10)
        return True

    return False


def go_to_sleeeeeeep(wait=60):
    escape_sleep = False

    while not escape_sleep:
        print('sleeping for {} seconds at {}...'.format(wait, datetime.now().strftime('%Y-%m-%d %I:%M:%S')))
        time.sleep(wait)

        escape_sleep = test_client_api_calls(
            {'tumblr_client': fetch_tumblr_client()},
             config_dictionary['run_options']['continuous_run'], True
        )

    return


def do_tumblr_like(runtime_options, post_to_like):
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    post_keys = get_post_keys(post_to_like)
    print('liking: {}, {}'.format(post_keys, post_to_like))
    runtime_options['tumblr_client'].like(post_keys['id'], post_keys['reblog_key'])


def do_tumblr_unlike(runtime_options, post_to_like):
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    post_keys = get_post_keys(post_to_like)
    print('unliking: {}, {}'.format(post_keys, post_to_like))
    runtime_options['tumblr_client'].unlike(post_keys['id'], post_keys['reblog_key'])


def do_tumblr_follow(runtime_options, blog_to_follow):
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    reduced_blog_url = reduce_blog_url(blog_to_follow['url'])
    print('following: {}'.format(reduced_blog_url))
    runtime_options['tumblr_client'].follow(blog_to_follow['url'])


def do_tumblr_unfollow(runtime_options, blog_to_unfollow):
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    reduced_blog_url = reduce_blog_url(blog_to_unfollow['url'])
    print('unfollowing: {}'.format(reduced_blog_url))
    runtime_options['tumblr_client'].unfollow(reduced_blog_url)


def next_page_of_follows(runtime_options, working_page={'page_offset': 0}):
    # keep
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    response_contains_errors = True
    tumblr_response = {}
    while response_contains_errors == True:
        tumblr_response = runtime_options['tumblr_client'].following()
        response_contains_errors = throttle_call(tumblr_response)

    working_page['blogs'] = tumblr_response['blogs']
    working_page['page_offset'] = working_page['page_offset'] + len(working_page['blogs'])
    return working_page


def next_page_of_likes(runtime_options, working_page={'page_offset': 0}):
    # keep
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    response_contains_errors = True
    tumblr_response = {}
    while response_contains_errors == True:
        tumblr_response = runtime_options['tumblr_client'].likes(
            offset=working_page['page_offset']
        )

        response_contains_errors = throttle_call(tumblr_response)

    working_page['likes'] = tumblr_response['liked_posts']
    working_page['page_offset'] = working_page['page_offset'] + len(working_page['likes'])
    return working_page


def next_page_of_posts(runtime_options, working_page={'page_offset': 0}):
    # keep
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])
    response_contains_errors = True
    tumblr_response = {}
    while response_contains_errors == True:
        tumblr_response = runtime_options['tumblr_client'].posts(
            runtime_options['user_params']['blog_name'],
            limit=10, offset=working_page['page_offset']
        )
        response_contains_errors = throttle_call(tumblr_response)

    working_page['posts'] = tumblr_response['posts']
    working_page['page_offset'] = working_page['page_offset'] + len(working_page['posts'])
    return working_page


def reduce_blog_url(blog_name):
    reduced = blog_name
    reduced = reduced.replace('http://', '')
    reduced = reduced.replace('https://', '')
    if reduced[-1:] == '/':
        reduced = reduced[:-1]

    return reduced


def reduce_like(like, path_to_captures):
    like_type = get_like_type(like)
    liked_url_hash = get_liked_url_hash(like)
    reduced_like_body = {
        'like_type': like_type,
        'liked_url_hash': liked_url_hash,
        'payload': get_capture_list_from_like(like, like_type),
        'path_to_captures': path_to_captures
    }
    return reduced_like_body


def reduce_url_file_name(url):
    return url[str.rfind(url, '/') + 1:]


def should_run_follows(config_dictionary):
    if any([config_dictionary['follows']['archive'],
            config_dictionary['follows']['unfollow'],
            config_dictionary['follows']['refollow']
            ]):
        return True

    return False

def should_run_likes(config_dictionary):
    if any([config_dictionary['likes']['archive'],
            config_dictionary['likes']['capture'],
            config_dictionary['likes']['unlike'],
            config_dictionary['likes']['relike']
            ]):
        return True

    return False

def should_run_posts(config_dictionary):
    if any([config_dictionary['posts']['archive'],
            config_dictionary['posts']['delete']
            ]):
        return True

    return False

def run_follow_pages(runtime_options, config_dictionary):
    # keep
    page_of_follows = next_page_of_follows(runtime_options)

    if (config_dictionary['follows']['archive']):
        file_full_of_json = open(runtime_options['follows_archive_path'], 'x', newline='\n', encoding='utf-8')

    while len(page_of_follows['blogs']) > 0:
        for blog in page_of_follows['blogs']:

            if (config_dictionary['follows']['archive']):
                # blog['description'] = cleanse_newlines(blog['description'])
                file_full_of_json.write(json.dumps(blog) + '\n')

            if (config_dictionary['follows']['unfollow']):
                do_tumblr_unfollow(runtime_options, blog)

        page_of_follows = next_page_of_follows(runtime_options, page_of_follows)

    if (config_dictionary['follows']['archive']):
        file_full_of_json.close()


def run_like_pages(runtime_options, config_dictionary):
    # keep
    page_of_likes = next_page_of_likes(runtime_options)

    if (config_dictionary['likes']['archive']):
        file_full_of_json = open(runtime_options['likes_archive_path'], 'x', newline='\n', encoding='utf-8')

    if (config_dictionary['likes']['capture']):
        directory_list = get_dir_list_less_dirs(runtime_options['path_to_captures'])
        directory_list = remove_dirs_from_dir_listing(directory_list)

    while len(page_of_likes['likes']) > 0:
        for like in page_of_likes['likes']:

            if (config_dictionary['likes']['archive']):
                # blog['description'] = cleanse_newlines(blog['description'])
                file_full_of_json.write(json.dumps(like) + '\n')

            if config_dictionary['likes']['capture']:
                reduced_like = reduce_like(like, runtime_options['path_to_captures'])
                smart_capture(reduced_like, directory_list)

            if (config_dictionary['likes']['unlike']):
                do_tumblr_unlike(runtime_options, like)

        page_of_likes = next_page_of_likes(runtime_options, page_of_likes)

    if (config_dictionary['likes']['archive']):
        file_full_of_json.close()


def run_post_pages(runtime_options, config_dictionary):
    # keep
    page_of_posts = next_page_of_posts(runtime_options)

    if (config_dictionary['posts']['archive']):
        file_full_of_json = open(runtime_options['posts_archive_path'], 'x', newline='\n', encoding='utf-8')

    while len(page_of_posts['posts']) > 0:
        for post in page_of_posts['posts']:

            if (config_dictionary['posts']['archive']):
                # blog['description'] = cleanse_newlines(blog['description'])
                file_full_of_json.write(json.dumps(post) + '\n')

            if (config_dictionary['posts']['delete']):
                do_tumblr_unfollow(runtime_options, post)

        page_of_posts = next_page_of_posts(runtime_options, page_of_posts)

    if (config_dictionary['posts']['archive']):
        file_full_of_json.close()

def run_files_to_refollow(runtime_options):
    # keep
    directory_list = focus_list(runtime_options['directory_list'], 'follows')

    for directory_item in directory_list:
        path_to_directory_item = os.path.join(runtime_options['path_to_archives'], directory_item)

        refollow_array = list()
        with open(path_to_directory_item) as file_in:
            for file_line in file_in:
                record = json.loads(file_line)
                refollow_array.append(record)

        for refollow in refollow_array:
            do_tumblr_follow(runtime_options, refollow)


def run_files_to_relike(runtime_options):
    # keep
    directory_list = focus_list(runtime_options['directory_list'], 'likes')

    for directory_item in directory_list:
        path_to_directory_item = os.path.join(runtime_options['path_to_archives'], directory_item)

        relike_array = list()
        with open(path_to_directory_item) as file_in:
            for file_line in file_in:
                record = json.loads(file_line)
                relike_array.append(record)

        for relike in relike_array:
            do_tumblr_like(runtime_options, relike)


def main():
    runtime_options = {}
    runtime_options['date_started'] = datetime.now().strftime('%y%m%d_%H%M%S')

    runtime_options['tumblr_client'] = fetch_tumblr_client()
    test_client_api_calls(runtime_options, config_dictionary['run_options']['continuous_run'])

    runtime_options['user_params'] = runtime_options['tumblr_client'].info()['user']
    runtime_options['user_params']['blog_name'] = runtime_options['user_params']['blogs'][0]['name']
    runtime_options['user_params']['url'] = runtime_options['user_params']['blogs'][0]['url']

    runtime_options['path_to_archives'] = '../resources/archives/'
    runtime_options['path_to_captures'] = '../resources/captures/'

    runtime_options['directory_list'] = get_dir_list_less_dirs(runtime_options['path_to_archives'])
    runtime_options['directory_list'] = remove_dirs_from_dir_listing(runtime_options['directory_list'])

    runtime_options['follows_archive_path'] = '{}follows_{}.txt'.format(runtime_options['path_to_archives'],
                                                                        runtime_options['date_started'])
    runtime_options['likes_archive_path'] = '{}likes_{}.txt'.format(runtime_options['path_to_archives'],
                                                                    runtime_options['date_started'])
    runtime_options['posts_archive_path'] = '{}posts_{}.txt'.format(runtime_options['path_to_archives'],
                                                                    runtime_options['date_started'])


    if (should_run_follows(config_dictionary)):
        run_follow_pages(runtime_options, config_dictionary)

        if config_dictionary['follows']['refollow']:
            run_files_to_refollow(runtime_options)

    if (should_run_likes(config_dictionary)):
        run_like_pages(runtime_options, config_dictionary)

        if config_dictionary['likes']['relike']:
            run_files_to_relike(runtime_options)

    if (should_run_posts(config_dictionary)):
        run_post_pages(runtime_options, config_dictionary)

    if config_dictionary['supplemental_editor']['do'] == 'unfollow' or config_dictionary['supplemental_editor'][
        'do'] == 'follow':
        print('supplemental edits is not yet implemented')

    exit()


main()
