import uuid
from django.utils.timezone import now, timedelta
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework.authtoken.models import Token
from .managers import CustomUserManager



class AccountModel(AbstractUser):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )
    username = None
    email = models.EmailField('email address', unique=True)
    is_staff = models.BooleanField(
        null=True,
        blank=True,
        default=True
    )
    first_name = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )
    birthday = models.DateField(
        null=True,
        blank=True
    )
    nickname = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        db_table = 'tb_user'


@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(instance.user.id, filename)


class RepoObjectModel(models.Model):
    repo_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )
    upload = models.FileField(
        upload_to=user_directory_path
    )
    
    class Meta:
        verbose_name = 'repo_object'
        verbose_name_plural = 'repo_objects'
        db_table = 'tb_repo_object'


class RepoModel(models.Model):
    repo_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )
    repo_name = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    repo_owner = models.ForeignKey(
        AccountModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    repo_description = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    repo_object_link = models.ForeignKey(
        RepoObjectModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'repo'
        verbose_name_plural = 'repos'
        db_table = 'tb_repo'
