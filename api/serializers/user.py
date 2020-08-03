from rest_framework import serializers
from django.contrib.auth.models import User, Group


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %X")
    last_login = serializers.DateTimeField(format="%Y-%m-%d %X")
    
    class Meta:
        ordering = ['-id']
        model = User
        fields = ("username", "role", 'last_login', 'date_joined', 'is_active')
    
    def get_role(self, instance):
        return Group.objects.filter(user=instance).first().name


class UserInfoSerializer(serializers.ModelSerializer):
    # group_name = str(Group.objects.get(id= groups))
    role = serializers.SerializerMethodField()
    
    class Meta:
        ordering = ['-id']
        model = User
        fields = ('username', 'role',)
    
    def get_role(self, instance):
        return Group.objects.filter(user=instance).first().name
