from django.urls import path, re_path

from rest_app.views import PostAPIView, UserCreationApiView, LikeAPIView

urlpatterns = [

    path('post/', PostAPIView.as_view(), name='posts'),
    path('user/', UserCreationApiView.as_view()),
    path('like/', LikeAPIView.as_view())
]
