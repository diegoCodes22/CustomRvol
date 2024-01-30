from datetime import datetime
from time import sleep

t1 = datetime.now()
sleep(10)
t2 = datetime.now()

diff = t2 - t1
print(diff.total_seconds() / 60)