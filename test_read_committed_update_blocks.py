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
def test_read_committed_update_blocks():
    # We check that an read committed UPDATE can block, by holding open a
    # concurrent UPDATE

    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier = threading.Barrier(2)

    def update_with_sleep():
        with transaction.atomic():
            Sock.objects.all().update(colour='black')
            barrier.wait()
            time.sleep(11)

    time_to_update_read_committed = None
    def update_read_committed():
        nonlocal time_to_update_read_committed
        with transaction.atomic():
	        barrier.wait()
	        start = time.time()
	        Sock.objects.all().update(colour='black')
	        end = time.time()
	        time_to_update_read_committed = end - start

    update_with_sleep_thread = threading.Thread(target=update_with_sleep)
    update_with_sleep_thread.start()
    update_read_committed_thread = threading.Thread(target=update_read_committed)
    update_read_committed_thread.start()

    update_with_sleep_thread.join()
    update_read_committed_thread.join()

    assert time_to_update_read_committed >= 10.0
