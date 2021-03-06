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
    # We construct a situation where committed in the database, we always have
    # num_socks/2 socks with 10 hits. We run an update of socks with 10 hits
    # to +1 the hits. Thus we would expect to get num_socks/2 affected rows.
    # However, due to a concurrent update, we get exactly 0.

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
        Sock.objects.all().update(hits=F('hits')+1)

    num_affected = None
    def update_with_10_hits():
        nonlocal num_affected
        barrier.wait()
        time.sleep(0.5)
        num_affected = Sock.objects.filter(hits=10).update(hits=F('hits')+1)

    update_all_thread = threading.Thread(target=update_all)
    update_all_thread.start()
    update_with_10_hits_thead = threading.Thread(target=update_with_10_hits)
    update_with_10_hits_thead.start()

    update_all_thread.join()
    update_with_10_hits_thead.join()

    assert num_affected == 0
