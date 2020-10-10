##############
# Setup Django

import django
django.setup()


#############
# Test proper

import threading
import time
import pytest
from django.db import connection, transaction
from django.db.models import F, Subquery

from app.models import Sock


@pytest.mark.django_db
def test_repeatable_read_concurrent_see_same_snapshot():
    def create():
        Sock.objects.all().delete()
        Sock.objects.create(id_a=1, id_b=1, colour='black')

    create_thread = threading.Thread(target=create)
    create_thread.start()
    create_thread.join()

    barrier_1 = threading.Barrier(3)
    barrier_2 = threading.Barrier(3)
    barrier_3 = threading.Barrier(3)
    barrier_4 = threading.Barrier(3)

    def update_multiple_transactions():
        with transaction.atomic():
            Sock.objects.all().update(colour='white')
            barrier_1.wait()
            barrier_2.wait()

        with transaction.atomic():
            Sock.objects.all().update(colour='black')
            barrier_3.wait()
            barrier_4.wait()

    colour_1_1 = None
    colour_1_2 = None
    def select_single_repeatable_read_1():
        nonlocal colour_1_1
        nonlocal colour_1_2
        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')

            barrier_1.wait()
            colour_1_1 = Sock.objects.get(id_a=1).colour
            barrier_2.wait()
            barrier_3.wait()
            colour_1_2 = Sock.objects.get(id_a=1).colour
            barrier_4.wait()

    colour_2_1 = None
    colour_2_2 = None
    def select_single_repeatable_read_2():
        nonlocal colour_2_1
        nonlocal colour_2_2
        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')

            barrier_1.wait()
            colour_2_1 = Sock.objects.get(id_a=1).colour
            barrier_2.wait()
            barrier_3.wait()
            colour_2_2 = Sock.objects.get(id_a=1).colour
            barrier_4.wait()

    update_multiple_transactions_thread = threading.Thread(target=update_multiple_transactions)
    update_multiple_transactions_thread.start()
    select_single_repeatable_read_1_thread = threading.Thread(target=select_single_repeatable_read_1)
    select_single_repeatable_read_1_thread.start()
    select_single_repeatable_read_2_thread = threading.Thread(target=select_single_repeatable_read_2)
    select_single_repeatable_read_2_thread.start()

    update_multiple_transactions_thread.join()
    select_single_repeatable_read_1_thread.join()
    select_single_repeatable_read_2_thread.join()

    # Assert that with multiple repeatable read atomic blocks, they see the
    # can see the same snapshot, that doesn't change
    assert colour_1_1 == 'black'
    assert colour_1_2 == 'black'
    assert colour_2_1 == 'black'
    assert colour_2_2 == 'black'
