import ast
import csv
import hashlib
import html
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
    else:
        list_to_include = ['like']

    for object_in_list in object_list:
        for search_term in list_to_include:
            if search_term in object_in_list:
                new_list.append(object_in_list)

    return new_list


def reduce_blog_url(blog_name):
    reduced = blog_name
    reduced = reduced.replace('http://', '')
    reduced = reduced.replace('https://', '')
    if reduced[-1:]:
        reduced = reduced[:-1]

    return reduced


def reduce_url_file_name(url):
    return url[str.rfind(url, '/') + 1:]


def get_file_extension_from_name(file_name):
    return file_name[-4:]


def get_complete_dir_listing(dir_to_list):
    return os.listdir(dir_to_list)


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
        print(like)
        return 'video'

    return


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


def smart_capture(reduced_like, known_files):
    # if reduced_like['like_type'] == 'video_vine':
    #     print('enter debug')

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


def read_csv(csv_path, likes_follows_or_posts='likes'):
    relike_array = []
    known_likes = []
    if likes_follows_or_posts in csv_path:
        with open(csv_path, newline='\n', encoding='utf-8') as csv_infile:
            csv_reader = csv.DictReader(csv_infile, delimiter=',', quotechar='"', escapechar='\\',
                                        lineterminator='\r\n')
            for record in csv_reader:
                if record['id'] + record['reblog_key'] not in known_likes:
                    known_likes.append(record['id'] + record['reblog_key'])
                    relike_array.append({'id': record['id'], 'reblog_key': record['reblog_key']})

    return relike_array


def next_page_of_likes(tumblr_client, page_of_likes={'page_offset': 0}):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    page_of_likes['likes'] = tumblr_client.likes(limit=10, offset=page_of_likes['page_offset'])['liked_posts']
    page_of_likes['page_offset'] = page_of_likes['page_offset'] + 10
    return page_of_likes


def next_page_of_follows(tumblr_client, page_of_blogs={'page_offset': 0}):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    page_of_blogs['blogs'] = tumblr_client.following(limit=10, offset=page_of_blogs['page_offset'])['blogs']
    page_of_blogs['page_offset'] = page_of_blogs['page_offset'] + 10
    return page_of_blogs


def next_page_of_posts(tumblr_client, page_of_posts={'page_offset': 0}):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])

    if 'reduced_blog_url' not in page_of_posts:
        page_of_posts['reduced_blog_url'] = reduce_blog_url(tumblr_client.info()['user']['blogs'][0]['url'])

    page_of_posts['posts'] = tumblr_client.posts(page_of_posts['reduced_blog_url'], limit=10,
                                                 offset=page_of_posts['page_offset'])['posts']
    page_of_posts['page_offset'] = page_of_posts['page_offset'] + 10
    return page_of_posts


def get_post_keys(likeable_post):
    likeable_keys = {'id': likeable_post['id'], 'reblog_key': likeable_post['reblog_key']}
    return likeable_keys


def get_blog_keys(tumblr_blog):
    if type(tumblr_blog) is dict:
        if 'url' in tumblr_blog:
            return {'reduced_url': reduce_blog_url(tumblr_blog['url'])}

    else:
        print('bad blog format recieved: {}'.format(tumblr_blog))
        print('exiting')
        exit()


def tumblr_like(tumblr_client, post_to_like):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    post_keys = get_post_keys(post_to_like)
    print('liking: {}, {}'.format(post_keys, post_to_like))
    tumblr_client.like(post_keys['id'], post_keys['reblog_key'])


def tumblr_unlike(tumblr_client, post_to_like):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    post_keys = get_post_keys(post_to_like)
    print('unliking: {}, {}'.format(post_keys, post_to_like))
    tumblr_client.unlike(post_keys['id'], post_keys['reblog_key'])


def tumblr_unfollow(tumblr_client, blog_to_follow):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    blog_keys = get_blog_keys(blog_to_follow)
    print('unfollowing: {}'.format(blog_keys['reduced_url']))
    tumblr_client.unfollow(blog_keys['reduced_url'])


def tumblr_follow(tumblr_client, blog_to_follow):
    test_client_api_calls(config_dictionary['run_options']['continuous_run'])
    blog_keys = get_blog_keys(blog_to_follow)
    print('following: {}'.format(blog_keys['reduced_url']))
    tumblr_client.follow(blog_keys['reduced_url'])


def fetch_tumblr_client():
    return pytumblr.TumblrRestClient(
        secrets['consumer_key'],
        secrets['consumer_secret'],
        secrets['oauth_token'],
        secrets['oauth_secret'])


def test_client_api_calls(continuous_run=False, escape_check=False):
    tumblr_tester = fetch_tumblr_client()

    tumblr_response = tumblr_tester.info()

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


def go_to_sleeeeeeep():
    escape_sleep = False

    while not escape_sleep:
        print('sleeping 1 minute at {}...'.format(datetime.now().strftime('%Y-%m-%d %I:%M:%S')))
        time.sleep(60)

        escape_sleep = test_client_api_calls(config_dictionary['run_options']['continuous_run'], True)

    return


def main():
    tumblr_client = fetch_tumblr_client()

    date_started_formatted = datetime.now().strftime('%y%m%d_%H%M%S')

    path_to_archives = '../resources/archives/'
    path_to_captures = '../resources/captures/'
    csv_path_followes = '{}follows_{}.csv'.format(path_to_archives, date_started_formatted)
    csv_path_likes = '{}likes_{}.csv'.format(path_to_archives, date_started_formatted)

    if config_dictionary['follows']['archive']:
        page_of_follows = next_page_of_follows(tumblr_client)

        with open(csv_path_followes, 'x', newline='\n', encoding='utf-8') as csv_file:
            csv_fieldnames = ['name', 'title', 'url', 'uuid', 'updated', 'description']
            csv_writer = csv.DictWriter(csv_file,
                                        csv_fieldnames,
                                        delimiter=',',
                                        quotechar='"',
                                        quoting=csv.QUOTE_ALL,
                                        escapechar='\\',
                                        lineterminator='\r\n')
            csv_writer.writeheader()

            while len(page_of_follows['blogs']) > 0:
                for blog in page_of_follows['blogs']:
                    blog['description'] = cleanse_newlines(blog['description'])
                    csv_writer.writerow(blog)

                page_of_follows = next_page_of_follows(tumblr_client, page_of_follows)

    if config_dictionary['follows']['unfollow']:
        page_of_follows = next_page_of_follows(tumblr_client)

        while len(page_of_follows['blogs']) > 0:
            for blog in page_of_follows['blogs']:
                tumblr_unfollow(tumblr_client, blog)

            page_of_follows = next_page_of_follows(tumblr_client, {'page_offset': 0})

    if config_dictionary['follows']['refollow']:
        directory_list = get_complete_dir_listing(path_to_archives)
        directory_list = remove_dirs_from_dir_listing(directory_list)
        directory_list = focus_list(directory_list, 'follows')

        for directory_item in directory_list:
            path_to_directory_item = os.path.join(path_to_archives, directory_item)
            if directory_item[-4:] == '.csv':
                refollow_array = read_csv(os.path.join(path_to_archives, directory_item))
            else:
                refollow_array = list()
                with open(path_to_directory_item) as file_in:
                    for file_line in file_in:
                        record = ast.literal_eval(file_line)
                        refollow_array.append(record)

            for refollow in refollow_array:
                tumblr_follow(tumblr_client, refollow)

    if config_dictionary['likes']['archive']:
        page_of_likes = next_page_of_likes(tumblr_client)

        with open(csv_path_likes, 'x', newline='\n', encoding='utf-8') as csv_file:
            csv_fieldnames = ['title', 'type', 'blog_name', 'blog', 'id', 'post_url', 'slug', 'date', 'timestamp',
                              'state', 'format', 'reblog_key', 'tags', 'short_url', 'should_open_in_legacy',
                              'recommended_source', 'recommended_color', 'followed', 'liked', 'note_count',
                              'video_url', 'html5_capable', 'thumbnail_url', 'thumbnail_width',
                              'thumbnail_height', 'duration', 'player', 'video_type', 'liked_timestamp', 'can_like',
                              'can_reblog', 'can_send_in_message', 'can_reply', 'display_avatar', 'image_permalink',
                              'link_url', 'source_url', 'source_title', 'photos', 'body', 'photoset_layout',
                              'post_author', 'permalink_url', 'post_author_is_adult', 'is_submission', 'plays', 'embed',
                              'audio_type', 'audio_url', 'audio_source_url', 'asking_name', 'asking_url', 'question',
                              'answer', 'bookmarklet']
            csv_writer = csv.DictWriter(csv_file,
                                        csv_fieldnames,
                                        delimiter=',',
                                        quotechar='"',
                                        quoting=csv.QUOTE_ALL,
                                        escapechar='\\',
                                        lineterminator='\r\n')
            csv_writer.writeheader()

            while len(page_of_likes['likes']) > 0:
                for liked in page_of_likes['likes']:

                    if 'body' in liked:
                        liked['body'] = cleanse_newlines(liked['body'])

                    if 'caption' in liked:
                        liked.pop('caption', None)

                    if 'name' in liked:
                        liked['name'] = cleanse_newlines(liked['name'])

                    if 'reblog' in liked:
                        liked.pop('reblog', None)

                    if 'summary' in liked:
                        liked.pop('summary', None)

                    if 'trail' in liked:
                        liked.pop('trail', None)

                    csv_writer.writerow(liked)

                    if config_dictionary['likes']['capture_binaries']:
                        photos_record = liked.photos
                        print(photos_record)

                page_of_likes = next_page_of_likes(tumblr_client, page_of_likes)

    if config_dictionary['likes']['unlike']:
        page_of_likes = next_page_of_likes(tumblr_client)

        while len(page_of_likes['likes']) > 0:
            for liked in page_of_likes['likes']:
                tumblr_unlike(tumblr_client, liked)

            page_of_likes = next_page_of_likes(tumblr_client, page_of_likes)

    if config_dictionary['likes']['relike']:
        directory_list = get_complete_dir_listing(path_to_archives)
        directory_list = remove_dirs_from_dir_listing(directory_list)
        directory_list = focus_list(directory_list, 'likes')

        for directory_item in directory_list:
            path_to_directory_item = os.path.join(path_to_archives, directory_item)
            if directory_item[-4:] == '.csv':
                relike_array = read_csv(os.path.join(path_to_archives, directory_item))
            else:
                relike_array = list()
                with open(path_to_directory_item) as file_in:
                    for file_line in file_in:
                        record = ast.literal_eval(file_line)
                        relike_array.append(record)

            for relike in relike_array:
                tumblr_like(tumblr_client, relike)

    if config_dictionary['posts']['delete']:
        page_of_posts = next_page_of_posts(tumblr_client)
        while len(page_of_posts['posts']) > 0:
            for post in page_of_posts['posts']:
                tumblr_client.delete_post(page_of_posts['reduced_blog_url'], post['id'])

    if config_dictionary['likes']['capture']:
        page_of_likes = next_page_of_likes(tumblr_client)

        directory_list = get_complete_dir_listing(path_to_captures)
        directory_list = remove_dirs_from_dir_listing(directory_list)

        while len(page_of_likes['likes']) > 0:
            for like in page_of_likes['likes']:
                reduced_like = reduce_like(like, path_to_captures)
                smart_capture(reduced_like, directory_list)

            page_of_likes = next_page_of_likes(tumblr_client, page_of_likes)

    if config_dictionary['posts']['archive']:
        print('archiving posts is not yet implemented')

    if config_dictionary['supplemental_editor']['do'] == 'unfollow' or config_dictionary['supplemental_editor'][
        'do'] == 'follow':
        print('supplemental edits is not yet implemented')

    exit()


main()
