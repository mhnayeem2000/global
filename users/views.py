from rest_framework import generics, permissions, viewsets, mixins, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import EmployeeManagementSerializer, ChangePasswordSerializer, RequestPasswordResetEmailSerializer, SetNewPasswordSerializer, UserManagementSerializer
from rest_framework.permissions import AllowAny , IsAdminUser
from .serializers import UserRegistrationSerializer , MyTokenObtainPairSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, filters 
from rest_framework.permissions import IsAuthenticated
from .serializers import MyProfileSerializer 


User = get_user_model()

class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data.get("old_password")):
                return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            return Response({"message": "Password updated successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        
        if user.role == User.Role.EMPLOYEE and not user.is_active:
            return Response(
                {"message": "Registration successful. Your account is pending approval by an administrator."},
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        else:
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PendingEmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeManagementSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.EMPLOYEE, is_active=False)
    



class ApproveEmployeeView(APIView):
    permission_classes = [IsOwnerOrReadOnly]
    def post(self, request, user_id, *args, **kwargs):
        try:
            user_to_approve = User.objects.get(id=user_id, role=User.Role.EMPLOYEE)
        except User.DoesNotExist:
            return Response(
                {"error": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if user_to_approve.is_active:
            return Response(
                {"message": "This employee is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_to_approve.is_active = True
        user_to_approve.save()
        return Response(
            {"message": f"Employee {user_to_approve.email} has been approved and activated."},
            status=status.HTTP_200_OK
        )

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserManagementViewSet(viewsets.ModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [IsOwnerOrReadOnly] 
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'first_name', 'last_name']
    
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or getattr(user, "role", None) != User.Role.OWNER:
            return User.objects.none()

        queryset = User.objects.all().order_by('-date_joined')
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())

        return queryset

    def get_permissions(self):
        user = self.request.user

        if user.is_authenticated:  
            if getattr(user, "role", None) == User.Role.OWNER:
                return [IsAuthenticated()]

        return [AllowAny()]
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MyProfileSerializer
        return UserManagementSerializer
    
class MyProfileViewSet(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = MyProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get_object(self):

        return self.request.user    
    

class RequestPasswordResetEmailView(generics.GenericAPIView):

    serializer_class = RequestPasswordResetEmailSerializer
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        serializer.send_password_reset_email(email)
        
        return Response(
            {"message": "If an account with this email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )
class SetNewPasswordView(generics.GenericAPIView):

    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


