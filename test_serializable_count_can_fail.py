##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import time
import pytest
from django.db import DatabaseError, connection, transaction
from django.db.models import F, Subquery
from app.models import Sock


@pytest.mark.django_db
def test_serializable_count_can_fail():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black', hits=1)
        Sock.objects.create(id_a=2, id_b=2, colour='white', hits=1)

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)
    barrier_3 = threading.Barrier(2)

    def serializable_a():
        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            Sock.objects.all().count()
            barrier_1.wait()
            Sock.objects.get(id_a=2).save()
        barrier_2.wait()

    caught = None
    def serializable_b():
        nonlocal caught
        try:
            with transaction.atomic():
                cursor = connection.cursor()
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                Sock.objects.all().count()
                barrier_1.wait()
                Sock.objects.get(id_a=1).save()
                barrier_2.wait()
        except Exception as exception:
            caught = exception

    serializable_a_thread = threading.Thread(target=serializable_a)
    serializable_a_thread.start()
    serializable_b_thread = threading.Thread(target=serializable_b)
    serializable_b_thread.start()

    serializable_a_thread.join()
    serializable_b_thread.join()

    assert isinstance(caught, DatabaseError)
    assert 'could not serialize access due to read/write dependencies among transactions' in caught.args[0]
