import configparser
import os
import uuid
from random import randint
from random import shuffle

import names
import requests
# Need this part to work with models, or we need to create management command
from django.db.models import Count
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trade_core.settings")
import django

django.setup()

from rest_app.models import Post, Like
from django.contrib.auth.models import User

config = configparser.ConfigParser()
config.read('config.ini')

number_of_users = int(config['DEFAULT']['number_of_users'])
max_posts_per_user = int(config['DEFAULT']['max_posts_per_user'])
max_likes_per_user = int(config['DEFAULT']['max_likes_per_user'])
HOST = 'http://127.0.0.1:8000/api/'
USER_CREATION_URL = 'user/'
POST_CREATION_URL = 'post/'
LIKE_URL = 'like/'
TOKEN_URL = 'token'


class Bot:
    def __init__(self):
        self.users = self.create_users_data()

    def create_users_data(self):
        users = []
        for _ in range(number_of_users):
            username = names.get_last_name().lower()
            email = '{}@gmail.com'.format(username)
            password = uuid.uuid4().hex
            users.append({'username': username, 'password': password, 'email': email})
        return users

    def user_signups(self):
        for user_data in self.users:
            response = requests.post('{}{}'.format(HOST, USER_CREATION_URL), json=user_data)
        print('User signup finished')

    @staticmethod
    def get_token(username, password):
        response = requests.post('{}{}'.format(HOST, TOKEN_URL), json={'username': username, 'password': password})

        return response.json()['token']

    def create_posts(self):
        for user_data in self.users:
            token = self.get_token(user_data['username'], user_data['password'])
            authorisation_header = {'Authorization': 'JWT {}'.format(token)}
            for _ in range(randint(0, max_posts_per_user)):
                response = requests.post('{}{}'.format(HOST, POST_CREATION_URL), json={'text': uuid.uuid4().hex},
                                         headers=authorisation_header)
        print("Create post finished")

    @staticmethod
    def _posts_to_like(user_id):
        # user can only like random posts from users who have at least one post with 0 likes
        # users cannot like their own posts
        users = User.objects.filter(~Q(id=user_id), posts__likes__isnull=True).distinct()
        posts = []
        for user in users:
            posts.extend(user.posts.all())
        return posts

    @staticmethod
    def _no_post_with_0_likes():
        return Post.objects.filter(likes__isnull=True)

    @staticmethod
    def _post_is_like_by_me(user_id, post_id):
        like = Like.objects.filter(user_id=user_id, post_id=post_id).first()
        return like

    def like_post(self, user):
        like_counter = 0
        user_id = user['user_id']
        username = User.objects.get(id=user_id).username

        # Retrieve saved password
        password = [i for i in self.users if i['username'] == username][0]['password']

        # Get token
        token = self.get_token(username, password)
        authorisation_header = {'Authorization': 'JWT {}'.format(token)}
        posts_to_like = self._posts_to_like(user_id)
        shuffle(posts_to_like)

        for post_to_like in posts_to_like:
            # if there is no posts with 0 likes, bot stops
            if not self._no_post_with_0_likes():
                return "There is not post with 0 like"
            # posts can be liked multiple times, but one user can like a certain post only once
            elif self._post_is_like_by_me(user_id, post_to_like.id):
                continue
            elif like_counter >= max_likes_per_user:
                return "User reach max like"
            else:
                like = requests.post('{}{}'.format(HOST, LIKE_URL), headers=authorisation_header,
                                     json={'post_id': post_to_like.id})
                like_counter += 1

        return True

    def like_posts_process(self):
        # next user to perform a like is the user who has most posts and has not reached max likes
        users_order_by_post_count = Post.objects.values('user_id').order_by().annotate(Count('id'))
        for user in users_order_by_post_count:
            self.like_post(user)


def erase_everything():
    """ Erase all data from previous bot run
        For testing purpose
    """
    Post.objects.all().delete()
    Like.objects.all().delete()
    User.objects.all().delete()


if __name__ == '__main__':
    erase_everything()
    bot = Bot()
    bot.user_signups()
    bot.create_posts()
    bot.like_posts_process()
