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
def test_serializable_fails_if_updating_different_rows():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')
        Sock.objects.create(id_a=2, id_b=2, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)
    barrier_3 = threading.Barrier(2)
    barrier_4 = threading.Barrier(2)

    def update_autocommit():
        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            barrier_1.wait()
            sock_1 = Sock.objects.get(id_a=1)
            sock_2 = Sock.objects.get(id_a=2)
            barrier_2.wait()
            sock_1.save()
            barrier_3.wait()
        barrier_4.wait()

    caught = None
    def update_serializable():
        nonlocal caught
        try:
            with transaction.atomic():
                cursor = connection.cursor()
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                barrier_1.wait()
                sock_1 = Sock.objects.get(id_a=1)
                sock_2 = Sock.objects.get(id_a=2)
                barrier_2.wait()
                barrier_3.wait()
                barrier_4.wait()
                sock_2.save()
        except Exception as exception:
            caught = exception

    update_autocommit_thread = threading.Thread(target=update_autocommit)
    update_autocommit_thread.start()
    update_serializable_thread = threading.Thread(target=update_serializable)
    update_serializable_thread.start()

    update_autocommit_thread.join()
    update_serializable_thread.join()

    assert isinstance(caught, DatabaseError)
    assert 'Canceled on identification as a pivot, during write' in caught.args[0]
