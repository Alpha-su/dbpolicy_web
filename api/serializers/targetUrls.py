from rest_framework import serializers
from ..models import Config, Location

class LocationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Location
        fields = "__all__"


class targetUrlSerializer(serializers.ModelSerializer):
    province = serializers.CharField(source="loc.province")
    city = serializers.CharField(source="loc.city")
    author = serializers.CharField(source="author.username")
    
    class Meta:
        model = Config
        fields = ("id", "province", "city", 'author', 'gov', 'is_active', "file_count", "target_url",
                  "item_pattern", "main_text_pattern", "date_pattern", "zupei_type", "source_pattern",
                  "title_pattern", "next_pattern", "action_pattern")