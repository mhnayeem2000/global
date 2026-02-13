from rest_framework import serializers
from .models import EmployeeAvailability, Appointment
from users.serializers import UserSerializer
from users.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

class EmployeeAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAvailability
        fields = ['id', 'employee', 'weekday', 'start_time', 'end_time']
        read_only_fields = ['employee']


class AppointmentSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    employee = UserSerializer(read_only=True)
    # employee_id is used for input (writing), but not shown in output
    employee_id = serializers.IntegerField(write_only=True)
    # email is for guest users input, not saved directly to appointment model
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Appointment
        fields = [
            'id', 'customer', 'employee', 'employee_id',
            'email', 'start_time', 'end_time', 'notes', 'status', 'meeting_link'
        ]
        read_only_fields = ['customer', 'status', 'meeting_link']

    def create(self, validated_data):
        # Extract fields that are not part of the Appointment model
        email = validated_data.pop('email', None)
        employee_id = validated_data.pop('employee_id')
        
        # Fetch the employee object
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
             raise serializers.ValidationError({"employee_id": "Invalid employee ID."})

        # Determine the customer
        request = self.context.get('request')
        request_user = request.user if request else None
        customer = None
        
        # 1. If user is logged in, they are the customer
        if request_user and request_user.is_authenticated:
            customer = request_user
            # Send a simple confirmation that booking was received
            self.send_booking_confirmation(customer)
        
        # 2. If guest, use the email provided
        elif email:
            customer, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'role': User.Role.CUSTOMER,
                    'first_name': 'Guest',
                    'last_name': 'User',
                }
            )

            if created:
                # NEW USER: Generate password and send "Welcome" email
                temp_password = get_random_string(length=10)
                customer.set_password(temp_password)
                customer.save()

                subject = "Welcome to Global Financial World - Account Created"
                message = (
                    f"Hi {customer.first_name},\n\n"
                    "You have successfully booked an appointment! An account has been created for you.\n\n"
                    "Please log in to manage your appointments using these credentials:\n"
                    f"Email: {customer.email}\n"
                    f"Temporary Password: {temp_password}\n\n"
                    "Thanks,\nGlobal Financial World Team"
                )
                self.send_email(customer.email, subject, message)
            else:
                # EXISTING USER (but not logged in): Send "Booking Received" email
                self.send_booking_confirmation(customer)

        else:
            # No login and no email provided
            raise serializers.ValidationError(
                {"email": "This field is required for guest bookings."}
            )

        # Create the appointment
        appointment = Appointment.objects.create(
            customer=customer,
            employee=employee,
            **validated_data
        )
        return appointment

    def send_booking_confirmation(self, user):
        """Helper to send a standard booking received email."""
        subject = "Appointment Request Received"
        message = (
            f"Hi {user.first_name},\n\n"
            "We have received your appointment request. Our team will review it and send you a confirmation link shortly.\n\n"
            "Thanks,\nGlobal Financial World Team"
        )
        self.send_email(user.email, subject, message)

    def send_email(self, to_email, subject, message):
        send_mail(
            subject,
            message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            fail_silently=False 
        )