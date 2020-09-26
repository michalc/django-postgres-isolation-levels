##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import time
import pytest
from django.db.models import F

from app.models import Sock


@pytest.mark.django_db
def test_autocommit_update_misses_rows():
    # We construct a situation where from a "committed" view of the database,
    # we always have num_socks/2 socks with 10 hits. We run a concurrent
    # update of socks with 10 hits to +1 the hits. Thus we should get
    # num_sock/2 with 11 hits. However, we get exactly 0

    num_socks = 500000

    def create():
        Sock.objects.all().delete()
        Sock.objects.bulk_create((
            Sock(
                id_a=i, id_b=i,
                hits=9 if i % 2 == 0 else 10,
                colour='black' if i % 2 == 0 else 'white',
            ) for i in range(0, num_socks)
        ))

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier = threading.Barrier(2)

    def update_all():
        barrier.wait()
        time.sleep(0.5)
        Sock.objects.all().update(hits=F('hits')+1)

    def update_with_10_hits():
        barrier.wait()
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
