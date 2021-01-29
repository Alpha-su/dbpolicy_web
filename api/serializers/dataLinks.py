from rest_framework import serializers
from ..models import Links, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"


class DataLinksSerializer(serializers.ModelSerializer):
    province = serializers.CharField(source="loc.province")
    city = serializers.CharField(source="loc.city")
    pub_date = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Links
        fields = ("id", "province", "city", 'gov', "sub_url", "zupei_type", "source", "title", "pub_date")
