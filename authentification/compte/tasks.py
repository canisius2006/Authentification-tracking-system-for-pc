from celery import shared_task

import time


@shared_task
def hello():

    time.sleep(10)

    print("Bonjour")

    return "OK"


@shared_task
def add(x,y):
    return x+y
