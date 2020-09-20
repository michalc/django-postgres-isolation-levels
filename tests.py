##############
# Setup Django

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'

import django
django.setup()


##############
# Tests proper

import threading
import random
import time
import pytest
from django.db import DatabaseError
from django.db.models import F

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


@pytest.mark.django_db
def test_autocommit_update_misses_rows():
    # We construct a situation where from a "committed" view of the database,
    # we always have num_socks/2 socks with 10 hits. We run a concurrent
    # update of socks with 10 hits to +1 the hits. Thus we should get
    # num_sock/2 with 11 hits. However, we get exactly 0

    num_socks = 50000

    def create():
        Sock.objects.all().delete()
        for i in range(0, num_socks):
            Sock.objects.create(
                id_a=i, id_b=i,
                hits=9 if i % 2 == 0 else 10,
                colour='black' if i % 2 == 0 else 'white',
            )

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier = threading.Barrier(2)

    def update_all():
        barrier.wait()
        Sock.objects.all().update(hits=F('hits')+1)

    def update_with_10_hits():
        barrier.wait()
        time.sleep(0.0001)  # Enough so the other query starts first
        Sock.objects.filter(hits=10).update(hits=F('hits')+1)

    update_all_thread = threading.Thread(target=update_all)
    update_all_thread.start()
    update_with_10_hits_thead = threading.Thread(target=update_with_10_hits)
    update_with_10_hits_thead.start()

    update_all_thread.join()
    update_with_10_hits_thead.join()

    num_11 = None
    def fetch_hits():
        nonlocal num_11
        num_11 = Sock.objects.filter(hits=11).count()

    fetch_hits_thread = threading.Thread(target=fetch_hits)
    fetch_hits_thread.start()
    fetch_hits_thread.join()

    assert num_11 == 0
