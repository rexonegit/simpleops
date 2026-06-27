from rest_framework import serializers
from .models import NetworkSegment, IPAddress, cmdbdatabase

class NetworkSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSegment
        fields = '__all__'

class IPAddressSerializer(serializers.ModelSerializer):
    network_segment_info = NetworkSegmentSerializer(source='network_segment', read_only=True)
    
    class Meta:
        model = IPAddress
        fields = '__all__'



class cmdbdatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = cmdbdatabase
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}  # 密码字段只写不读
        }