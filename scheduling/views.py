from rest_framework import viewsets, views, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.decorators import action
from datetime import datetime, time, timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import EmployeeAvailability, Appointment
from .serializers import EmployeeAvailabilitySerializer, AppointmentSerializer
from users.permissions import IsEmployeeOrOwner
from users.models import User 

class EmployeeAvailabilityViewSet(viewsets.ModelViewSet):

    serializer_class = EmployeeAvailabilitySerializer

    def get_permissions(self):

        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsEmployeeOrOwner()]

    def get_queryset(self):
   
        queryset = EmployeeAvailability.objects.all()
        user = self.request.user
        if self.action in ['update', 'partial_update', 'destroy']:
            if user.role == 'EMPLOYEE':
                return queryset.filter(employee=user)
            return queryset
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API for booking and managing appointments.
    """
    serializer_class = AppointmentSerializer
    # Default permission is authenticated, but we override for 'create'
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Allow guests (AllowAny) to CREATE appointments.
        Require Auth for everything else.
        """
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        # Guests (not logged in) cannot see any list
        if not user.is_authenticated:
            return Appointment.objects.none()

        # Employees/Owners see ALL appointments to manage them
        if user.role in ['EMPLOYEE', 'OWNER']:
            return Appointment.objects.all().order_by('start_time')
        
        # Customers only see THEIR own appointments
        return Appointment.objects.filter(customer=user).order_by('start_time')

    # NOTE: perform_create is REMOVED because the logic is now in Serializer.create

    @action(detail=True, methods=['patch'], permission_classes=[IsEmployeeOrOwner])
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = [choice[0] for choice in Appointment.Status.choices]
        if new_status not in valid_statuses:
            return Response({"error": f"Invalid status. Valid choices: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = new_status
        appointment.save()
            
        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsEmployeeOrOwner])
    def confirm_and_send_link(self, request, pk=None):
        """
        Confirms the appointment and sends the meeting link to the CUSTOMER.
        """
        appointment = self.get_object()
        meeting_link = request.data.get('meeting_link')

        if not meeting_link:
            return Response({"error": "A 'meeting_link' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.meeting_link = meeting_link
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()

        # Explicitly get the customer to ensure email goes to the right person
        customer = appointment.customer
        employee = appointment.employee
        
        subject = f"Your Appointment is Confirmed: {appointment.start_time.strftime('%B %d, %Y at %I:%M %p')}"
        message = f"""
Hi {customer.first_name},

Your appointment with {employee.first_name} has been confirmed.

Details:
Date: {appointment.start_time.strftime('%A, %B %d, %Y')}
Time: {appointment.start_time.strftime('%I:%M %p')} UTC

Meeting Link:
{appointment.meeting_link}

We look forward to speaking with you!

Thanks,
The Global Financial World Team
"""
        # Send email specifically to the customer's email address
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [customer.email],
            fail_silently=False
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SchedulingView(views.APIView):
    """
    Public endpoint to get available time slots.
    """
    permission_classes = [AllowAny] 

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')
        employee_id = request.query_params.get('employee_id')

        if not date_str or not employee_id:
            return Response({"error": "Both 'date' and 'employee_id' query parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = target_date.weekday()
        except ValueError:
            return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            availability = EmployeeAvailability.objects.get(employee_id=employee_id, weekday=weekday)
        except EmployeeAvailability.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)

        booked_appointments = Appointment.objects.filter(
            employee_id=employee_id,
            start_time__date=target_date
        )
        
        booked_slots = []
        for appt in booked_appointments:
            booked_slots.append((appt.start_time.time(), appt.end_time.time()))

        available_slots = []
        slot_start = datetime.combine(target_date, availability.start_time)
        day_end = datetime.combine(target_date, availability.end_time)

        durations = [10, 20, 30] 

        while slot_start < day_end:
            is_available = True
            for booked_start, booked_end in booked_slots:
                booked_start_dt = datetime.combine(target_date, booked_start)
                booked_end_dt = datetime.combine(target_date, booked_end)
                
                if slot_start < booked_end_dt and (slot_start + timedelta(minutes=min(durations))) > booked_start_dt:
                    is_available = False
                    break
            
            if is_available:
                longest_duration = max(durations)
                if slot_start + timedelta(minutes=longest_duration) <= day_end:
                     available_slots.append(slot_start.strftime('%H:%M'))

            slot_start += timedelta(minutes=min(durations))

        return Response(available_slots, status=status.HTTP_200_OK)
    

class PublicEmployeeListView(views.APIView):
    """
    Public endpoint to list employees so guests can choose who to book with.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        employees = User.objects.filter(role__in=['EMPLOYEE', 'OWNER'])
        data = [
            {
                "id": emp.id,
                "full_name": f"{emp.first_name} {emp.last_name}",
                "email": emp.email 
            }
            for emp in employees
        ]
        return Response(data, status=status.HTTP_200_OK)