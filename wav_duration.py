import wave
import contextlib
import sys


# fname = sys.argv[1]

fnames = r"""
E:\2024_Backup\Audio\SD-A\ZOOM0001\ZOOM0001_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0003\ZOOM0003_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0005\ZOOM0005_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0007\ZOOM0007_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0009\ZOOM0009_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0011\ZOOM0011_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0013\ZOOM0013_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0015\ZOOM0015_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0017\ZOOM0017_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0019\ZOOM0019_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0021\ZOOM0021_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0023\ZOOM0023_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0025\ZOOM0025_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0027\ZOOM0027_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0029\ZOOM0029_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0031\ZOOM0031_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0033\ZOOM0033_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0035\ZOOM0035_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0037\ZOOM0037_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0039\ZOOM0039_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0041\ZOOM0041_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0043\ZOOM0043_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0045\ZOOM0045_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0047\ZOOM0047_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0048\ZOOM0048_LR.WAV
E:\2024_Backup\Audio\SD-A\ZOOM0050\ZOOM0050_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0001\ZOOM0001_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0003\ZOOM0003_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0005\ZOOM0005_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0007\ZOOM0007_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0009\ZOOM0009_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0011\ZOOM0011_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0012\ZOOM0012_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0014\ZOOM0014_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0016\ZOOM0016_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0018\ZOOM0018_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0020\ZOOM0020_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0022\ZOOM0022_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0023\ZOOM0023_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0025\ZOOM0025_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0027\ZOOM0027_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0029\ZOOM0029_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0031\ZOOM0031_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0033\ZOOM0033_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0035\ZOOM0035_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0037\ZOOM0037_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0039\ZOOM0039_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0044\ZOOM0044_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0046\ZOOM0046_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0048\ZOOM0048_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0050\ZOOM0050_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0052\ZOOM0052_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0054\ZOOM0054_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0056\ZOOM0056_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0058\ZOOM0058_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0060\ZOOM0060_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0062\ZOOM0062_LR.WAV
E:\2024_Backup\Audio\SD-F\ZOOM0064\ZOOM0064_LR.WAV
""".split("\n")
fnames = [x for x in fnames if len(x) > 0]

tot = 0
for fname in fnames:
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration_s = frames / float(rate)
        m,s = divmod(duration_s,60)
        print(fname,m,s,sep="\t")
        tot += duration_s

print(tot)

