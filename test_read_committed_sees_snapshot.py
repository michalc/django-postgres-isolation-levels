##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import time
import pytest
from django.db import transaction
from django.db.models import F, Subquery

from app.models import Sock


@pytest.mark.django_db
def test_read_committed_sees_snapshot():
    # We check that an autocommit UPDATE can block, by holding open a
    # concurrent UPDATE

    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)
    barrier_3 = threading.Barrier(2)
    barrier_4 = threading.Barrier(2)

    def update_multiple_atomic():
        with transaction.atomic():
            Sock.objects.all().update(colour='white')
            barrier_1.wait()
            barrier_2.wait()

        with transaction.atomic():
            Sock.objects.all().update(colour='black')
            barrier_3.wait()
            barrier_4.wait()

    colour_1 = None
    colour_2 = None
    def select_single_atomic():
        nonlocal colour_1
        nonlocal colour_2
        with transaction.atomic():
            barrier_1.wait()
            colour_1 = Sock.objects.get(id_a=1).colour
            barrier_2.wait()
            barrier_3.wait()
            colour_2 = Sock.objects.get(id_a=1).colour
            barrier_4.wait()

    update_multiple_atomic_thread = threading.Thread(target=update_multiple_atomic)
    update_multiple_atomic_thread.start()
    select_single_atomic_thread = threading.Thread(target=select_single_atomic)
    select_single_atomic_thread.start()

    update_multiple_atomic_thread.join()
    select_single_atomic_thread.join()

    # Assert that in a single atomic block, we do see changing data from other
    # transactions, but not not-committed data
    assert colour_1 == 'black'
    assert colour_2 == 'white'
