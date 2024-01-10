from VolumeFrame import VolumeFrame


vf = VolumeFrame(symbol="SPY")


def entry_algorithm():
    if vf.purged["volume"].iloc[-1] > vf.avg_vol:
        print("2")



print(vf.avg_vol)

