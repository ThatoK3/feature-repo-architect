from rest_framework import serializers
from .models import Application, Function, UserAccess, FunctionAccess
from django.contrib.auth.models import User

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'name', 'url', 'description']

class FunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Function
        fields = ['id', 'name', 'description', 'application']

class UserAccessSerializer(serializers.ModelSerializer):
    functions = FunctionSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserAccess
        fields = ['id', 'user', 'application', 'functions']

class FunctionAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionAccess
        fields = ['id', 'user', 'function']


class LoginSerializers(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(max_length=255, required=False)
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        max_length=128,
        write_only=True
    )

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not (username or email) or not password:
            msg = _('Must include either "username" or "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        user = authenticate(request=self.context.get('request'), username=username, email=email, password=password)


        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        data['user'] = user
        return data


