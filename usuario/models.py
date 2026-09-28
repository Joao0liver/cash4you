from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O usuário deve possuir um e-mail.')

        email = self.normalize_email(email)

        usuario = self.model(
            email=email,
            nome=nome,
            **extra_fields
        )

        usuario.set_password(password)
        usuario.save(using=self._db)

        return usuario

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(
            email=email,
            nome=nome,
            password=password,
            **extra_fields
        )


class Usuario(AbstractUser):
    username = None

    nome = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        unique=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    objects = UsuarioManager()

    def __str__(self):
        return self.nome