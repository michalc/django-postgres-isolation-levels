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
def test_select_for_update_blocks():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier = threading.Barrier(2)

    def select_for_update_with_sleep():
        with transaction.atomic():
            list(Sock.objects.select_for_update().filter(id_a=1))
            barrier.wait()
            time.sleep(11)

    time_to_select_for_update = None
    def select_for_update():
        nonlocal time_to_select_for_update
        with transaction.atomic():
	        barrier.wait()
	        start = time.time()
	        list(Sock.objects.select_for_update().filter(id_a=1))
	        end = time.time()
	        time_to_select_for_update = end - start

    select_for_update_with_sleep_thread = threading.Thread(target=select_for_update_with_sleep)
    select_for_update_with_sleep_thread.start()
    select_for_update_thread = threading.Thread(target=select_for_update)
    select_for_update_thread.start()

    select_for_update_with_sleep_thread.join()
    select_for_update_thread.join()

    assert time_to_select_for_update >= 10.0
