from rest_framework import serializers
from .models import User


class SendCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)


class ActivateInviteSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    referrals = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['phone_number', 'invite_code', 'activated_invite_code', 'referrals']

    def get_referrals(self, obj):
        referrals = User.objects.filter(activated_invite_code=obj.invite_code)
        return [user.phone_number for user in referrals]