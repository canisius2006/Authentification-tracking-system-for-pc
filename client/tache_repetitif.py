from apscheduler.schedulers.blocking import BlockingScheduler


def notification():
    print("Notification envoyée")


scheduler = BlockingScheduler()

scheduler.add_job(
    notification,
    'interval',
    seconds=3
)

scheduler.start()