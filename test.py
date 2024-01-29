from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from time import perf_counter
from Config import Config


conf = Config(symbol='spy', duration="1800 S")
x = perf_counter()
hds = reqHistoricalDataStream(conf.CONN_VARS, conf.contract, conf.duration, conf.bar_size)
print(perf_counter() - x)
print(hds)
