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
def test_repeatable_read_can_fail():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)
    barrier_3 = threading.Barrier(2)

    def update_autocommit():
        sock = Sock.objects.get(id_a=1)
        barrier_1.wait()
        barrier_2.wait()
        sock.save()
        barrier_3.wait()

    caught = None
    def update_repeatable_read():
        nonlocal caught
        try:
            with transaction.atomic():
                cursor = connection.cursor()
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                barrier_1.wait()
                sock = Sock.objects.get(id_a=1)
                barrier_2.wait()
                barrier_3.wait()
                sock.save()
        except Exception as exception:
            caught = exception

    update_autocommit_thread = threading.Thread(target=update_autocommit)
    update_autocommit_thread.start()
    update_repeatable_read_thread = threading.Thread(target=update_repeatable_read)
    update_repeatable_read_thread.start()

    update_autocommit_thread.join()
    update_repeatable_read_thread.join()

    assert isinstance(caught, DatabaseError)
    assert 'could not serialize access due to concurrent update' in caught.args[0]
