import uuid
from django.db import models


class Person(models.Model):
    pass


class Sock(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    id_a = models.IntegerField(null=False, unique=True)
    id_b = models.IntegerField(null=False, unique=True)
    hits = models.IntegerField(null=False, default=0)
    person = models.ForeignKey('Person', null=False, on_delete=models.CASCADE),
    colour = models.CharField(
        max_length=64,
        choices=(('black', 'black'), ('white', 'white')),
        default='white',
        null=False,
    )
