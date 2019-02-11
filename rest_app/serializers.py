import requests
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_app.models import Post, Like
import clearbit

from trade_core.settings import CLEAR_BIT_API_KEY, HUNTER_API_KEY

clearbit.key = CLEAR_BIT_API_KEY


class PostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'text', 'publish_date']


class LikeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'


class LikeAPISerializer(serializers.Serializer):
    post_id = serializers.CharField()

    def validate_post_id(self, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise ValidationError("Post doesn't exists")
        return post

    def like(self):
        _, _ = Like.objects.get_or_create(
            user=self.context['user'],
            post=self.validated_data['post_id'],
            value=True
        )

    def dislike(self):
        _, _ = Like.objects.get_or_create(
            user=self.context['user'],
            post=self.validated_data['post_id'],
            value=False
        )


class UserListAPISerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()


class CreateUserAPISerizlizer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_username(self, username):
        user_obj = User.objects.filter(username=username)
        if len(user_obj) != 0:
            raise ValidationError("User with this username already exists")
        return username

    def validate_email(self, email):
        email_obj = User.objects.filter(email=email).exists()
        if email_obj:
            raise ValidationError("User with this username already exists")

        # Hunter implementation
        url = 'https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}'

        response = requests.get(url.format(email=email, api_key=HUNTER_API_KEY))
        if response.status_code == 200:
            if response.json()['data']['result'] == 'undeliverable':
                raise ValidationError('Provided email is undeliverable')

        return email

    def validate_password(self, password):
        return password

    def save(self, **kwargs):
        # Clear bit implementation
        # Need to pay for service.
        try:
            response = clearbit.Enrichment.find(email=self.validated_data['email'], stream=True)
            if response and 'person' in response:
                first_name = response['person']['name']['givenName']
                last_name = response['person']['name']['familyName']
            else:
                first_name, last_name = '', ''
        except:
            first_name, last_name = '', ''
        User.objects.create_user(**self.validated_data, first_name=first_name, last_name=last_name)
