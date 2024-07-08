from django.urls import path
from .views import (
    UserSignupView, UserLoginView, UserSearchView,
    FriendRequestView, accept_friend_request, reject_friend_request,
    FriendsListView
)

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='search'),
    path('friend-request/', FriendRequestView.as_view(), name='friend-request'),
    path('friend-request/accept/<int:request_id>/', accept_friend_request, name='accept-friend-request'),
    path('friend-request/reject/<int:request_id>/', reject_friend_request, name='reject-friend-request'),
    path('friends/', FriendsListView.as_view(), name='friends'),
]
