from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken # type: ignore
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer # type: ignore

class UserSignupView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        serializer.save()

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '').lower()
        password = request.data.get('password', '')
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword', '').lower()
        return CustomUser.objects.filter(
            Q(email__iexact=keyword) | Q(username__icontains=keyword)
        ).distinct()

class FriendRequestView(generics.ListCreateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, is_accepted=False)

    def create(self, request, *args, **kwargs):
        from_user = request.user
        to_user_id = request.data.get('to_user_id')
        to_user = CustomUser.objects.get(id=to_user_id)

        # Limit friend requests to 3 per minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if FriendRequest.objects.filter(from_user=from_user, timestamp__gte=one_minute_ago).count() >= 3:
            return Response({'error': 'Friend request limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        friend_request, created = FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user)
        if created:
            return Response({'status': 'Friend request sent'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_friend_request(request, request_id):
    friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user)
    friend_request.is_accepted = True
    friend_request.save()
    return Response({'status': 'Friend request accepted'})

@api_view(['post'])
@permission_classes([permissions.IsAuthenticated])
def reject_friend_request(request, request_id):
    friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user)
    friend_request.delete()
    return Response({'status': 'Friend request rejected'})

class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends = CustomUser.objects.filter(
            Q(sent_requests__to_user=user, sent_requests__is_accepted=True) |
            Q(received_requests__from_user=user, received_requests__is_accepted=True)
        ).distinct()
        return friends