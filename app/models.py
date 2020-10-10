import uuid
from django.db import models


class Sock(models.Model):
    id_a = models.IntegerField(null=False, unique=True)
    id_b = models.IntegerField(null=False, unique=True)
    hits = models.IntegerField(null=False, default=0)
    colour = models.CharField(
        max_length=64,
        choices=(('black', 'black'), ('white', 'white')),
        default='white',
        null=False,
    )
