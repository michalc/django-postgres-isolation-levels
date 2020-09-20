##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import random
import pytest
from django.db import DatabaseError

from app.models import Sock


@pytest.mark.django_db
def test_autocommit_update_deadlock():
    # We make a deadlock likely by updating the same rows, but in a way where
    # Postgres is likely to lock them in conflicting orders
    #
    # We do all database access in separate threads so they are not in the
    # transaction that pytest starts

    num_threads = 50
    ids = list(range(0, 1000))

    def create():
        Sock.objects.all().delete()
        for i in ids:
            Sock.objects.create(
                id_a=i,
                id_b=len(ids)-i,
                colour='black' if i % 2 == 0 else 'white',
            )

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier = threading.Barrier(num_threads)
    caught = [None] * num_threads

    def update(i):
        nonlocal caught
        sample_ids = random.sample(ids, int(len(ids) / 2))
        field = 'id_a' if i % 2 == 0 else 'id_b'

        try:
            barrier.wait()
            Sock.objects.filter(**{
                field + '__in': sample_ids
            }).update(colour='black')
        except Exception as exception:
            caught[i] = exception

    threads = [
        threading.Thread(target=update, args=(i,))
        for i in range(0, num_threads)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    exceptions = [e for e in caught if e is not None] 
    assert len(exceptions) > 0
    assert isinstance(exceptions[0], DatabaseError)
    assert 'deadlock' in exceptions[0].args[0]
