##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import random
import pytest
from django.db import DatabaseError, transaction

from app.models import Sock


@pytest.mark.django_db
def test_select_for_update_can_deadlock():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')
        Sock.objects.create(id_a=2, id_b=2, colour='white')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)

    caught = None
    def update_a():
        nonlocal caught
        try:
            with transaction.atomic():
                list(Sock.objects.select_for_update().filter(id_a=1))
                barrier_1.wait()
                barrier_2.wait()
                list(Sock.objects.select_for_update().filter(id_a=2))
        except Exception as exception:
            caught = exception

    def update_b():
        nonlocal caught
        try:
            with transaction.atomic():
                barrier_1.wait()
                list(Sock.objects.select_for_update().filter(id_a=2))
                barrier_2.wait()
                list(Sock.objects.select_for_update().filter(id_a=1))
        except Exception as exception:
            caught = exception

    update_a_thread = threading.Thread(target=update_a)
    update_a_thread.start()
    update_b_thread = threading.Thread(target=update_b)
    update_b_thread.start()

    update_b_thread.join()
    update_b_thread.join()

    assert isinstance(caught, DatabaseError)
    assert 'deadlock' in caught.args[0]
