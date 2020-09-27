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
def test_read_committed_update_succeeds():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(2)
    barrier_2 = threading.Barrier(2)

    update_a_done = False
    def update_a():
        nonlocal update_a_done
        with transaction.atomic():
            barrier_1.wait()
            Sock.objects.all().update(colour='black')
            time.sleep(1)
        update_a_done = True

    update_b_done = False
    def update_b():
        nonlocal update_b_done
        with transaction.atomic():
            barrier_1.wait()
            Sock.objects.all().update(colour='black')
            time.sleep(1)
        update_b_done = True

    update_a_thread = threading.Thread(target=update_a)
    update_a_thread.start()
    update_b_thread = threading.Thread(target=update_b)
    update_b_thread.start()

    update_a_thread.join()
    update_b_thread.join()

    assert update_a_done
    assert update_b_done
