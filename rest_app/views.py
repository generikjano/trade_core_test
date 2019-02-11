# Create your views here.
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_app.models import Post, Like
from rest_app.serializers import CreateUserAPISerizlizer, UserListAPISerializer, PostModelSerializer, \
    LikeModelSerializer, LikeAPISerializer


class PostAPIView(generics.ListCreateAPIView):
    """ Change subscriber """
    permission_classes = (IsAuthenticated,)
    serializer_class = PostModelSerializer

    def get_queryset(self):
        return Post.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LikeAPIView(APIView):
    serializer_class = LikeModelSerializer

    def get(self, request):
        return Response(LikeModelSerializer(Like.objects.filter(
            user=request.user
        ), many=True).data, )

    def post(self, request):
        """ Like post"""
        serialized = LikeAPISerializer(data=request.data, context={'user': request.user})
        if serialized.is_valid(raise_exception=True):
            serialized.like()
            return Response(serialized.data)
        else:
            return Response(serialized.errors)

    def delete(self, request):
        """ Dislike post"""
        serialized = LikeAPISerializer(data=request.data, context={'user': request.user})
        if serialized.is_valid(raise_exception=True):
            serialized.dislike()
            return Response(serialized.data)
        else:
            return Response(serialized.errors)


class UserCreationApiView(APIView):
    """ List of topups and add new topup to subscriber """
    serializer_class = CreateUserAPISerizlizer

    def get(self, request):
        serialized = UserListAPISerializer(User.objects.all(), many=True)
        return Response(serialized.data)

    def post(self, request, *args, **kwargs):
        serialized = CreateUserAPISerizlizer(data=request.data)
        if serialized.is_valid(raise_exception=True):
            serialized.save()
            data = serialized.data
            data.pop('password')
            return Response(data)
        else:
            return Response(serialized.errors)
