import numpy as np
import pyaudio
import audioop

NOTE_MIN = 36
NOTE_MAX = 96
FSAMP = 22050
FRAME_SIZE = 1024
FRAMES_PER_FFT = 16
THRESHOLD = 9000

SAMPLES_PER_FFT = FRAME_SIZE * FRAMES_PER_FFT
FREQ_STEP = float(FSAMP)/SAMPLES_PER_FFT

NOTE_NAMES = "C C# D D# E F F# G G# A A# B".split()

def f2n(f):
    return 69+12*np.log2(f/440.0)
def n2f(n):
    return 440*2.0**((n-69)/12.0)
def nn(n):
    return NOTE_NAMES[n%12]+str(int(n/12-1))
def n2fft(n):
    return n2f(n)/FREQ_STEP

imin = max(0,int(np.floor(n2fft(NOTE_MIN-1))))
imax = min(SAMPLES_PER_FFT,int(np.ceil(n2fft(NOTE_MAX+1))))

buf = np.zeros(SAMPLES_PER_FFT,dtype=np.float32)
frames = 0

stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                channels=1,
                                rate=FSAMP,
                                input=True,
                                frames_per_buffer=FRAME_SIZE)
stream.start_stream()

window = 0.5*(1-np.cos(np.linspace(0,2*np.pi,SAMPLES_PER_FFT,False)))

while stream.is_active():
    data = stream.read(FRAME_SIZE)
    buf[:-FRAME_SIZE] = buf[FRAME_SIZE:]
    buf[-FRAME_SIZE:] = np.fromstring(data,np.int16)
    fft = np.fft.rfft(buf*window)
    freq = (np.abs(fft[imin:imax]).argmax()+imin)*FREQ_STEP
    n = f2n(freq)
    n0 = int(round(n))
    volume = audioop.rms(data,2)
    frames += 1

    if (frames >= FRAMES_PER_FFT):
        if (volume >= THRESHOLD):
            print("Frequency: {:7.2f} hertz,    Note: {:>3s}    Volume: {:10.2f}".format(freq,nn(n0),volume))
        else:
            print("...")
