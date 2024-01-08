from VolumeFrame import VolumeFrame
from Config import Config


configs = Config(symbol="SPY")
vf = VolumeFrame(configs)

print(vf.purged)
print(vf.avg_vol)

