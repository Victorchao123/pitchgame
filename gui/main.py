import pygame
from pygame import *
import numpy as np
import pyaudio as pa
import audioop as ao
import statistics as st
import time

NOTE_MIN = 36
NOTE_MAX = 96
FSAMP = 22050
FRAME_SIZE = 1024
FRAMES_PER_FFT = 4

THRESHOLD = 10000  # Volume (RMS) must be >=THRESHOLD in order to register as playing a note
BPM       = 20     # Beats per minute
BIT       = 8      # Beats in total

SAMPLES_PER_FFT = FRAME_SIZE * FRAMES_PER_FFT
FREQ_STEP = float(FSAMP)/SAMPLES_PER_FFT
BEAT_DELAY = 30.0/BPM

def f2n(f):
    return 69+12*np.log2(f/440.0)
def n2f(n):
    return 440*2.0**((n-69)/12.0)
def n2fft(n):
    return n2f(n)/FREQ_STEP
def find_max_mode(list1):
    list_table = st._counts(list1)
    len_table = len(list_table)

    if len_table == 1:
        max_mode = st.mode(list1)
    else:
        new_list = []
        for i in range(len_table):
            new_list.append(list_table[i][0])
        max_mode = max(new_list) # use the max value here
    return max_mode

class Note:
    pitch = 0 # 0 if rest, otherwise semitone number (C4=60, C#4=61, D4=62, etc...)
    value = 1 # 1 if sixteenth, 2 if eighth, 3 if dotted eighth, 4 if quarter, ..., 8 if half, etc...

imin = max(0,int(np.floor(n2fft(NOTE_MIN-1))))
imax = min(SAMPLES_PER_FFT,int(np.ceil(n2fft(NOTE_MAX+1))))

buf = np.zeros(SAMPLES_PER_FFT,dtype=np.float32)
frames = 0

stream = pa.PyAudio().open(format=pa.paInt16,
                                channels=1,
                                rate=FSAMP,
                                input=True,
                                frames_per_buffer=FRAME_SIZE)
stream.start_stream()
window = 0.5*(1-np.cos(np.linspace(0,2*np.pi,SAMPLES_PER_FFT,False)))

# Get initial time
initt = time.time()

# Total samples per beat, and number of samples that were on for a beat
tspb = 0
cspb = 0

# Number of beats
beats = 0

# Whether note recording has started or not
rec = False

# How many beats have been recorded
rbeats = 0

# Frequencies of on samples
samp = []

# Output note array
notes = []

note = Note()
notes.append(note)
ol = -1

b = 0


while (stream.is_active() and rbeats < BIT):
    # Calculate stuff
    data = stream.read(FRAME_SIZE)
    buf[:-FRAME_SIZE] = buf[FRAME_SIZE:]
    buf[-FRAME_SIZE:] = np.fromstring(data,np.int16)
    fft = np.fft.rfft(buf*window)
    freq = (np.abs(fft[imin:imax]).argmax()+imin)*FREQ_STEP
    n = f2n(freq)
    n0 = int(round(n))
    volume = ao.rms(data,2)
    frames += 1
    
    if (frames >= FRAMES_PER_FFT):
        if (not initt):
            initt = time.time()

        # Beat counter
        if (time.time()-(beats+1)*BEAT_DELAY >= initt):
            beats += 1;
            tspb = 0;
            cspb = 0;
            if (rec):
                rbeats += 1

        # Calculate samples
        if (time.time()-(beats+1)*BEAT_DELAY < initt):
            tspb += 1;
            if (volume >= THRESHOLD):
                cspb += 1;
                samp.append(freq);

        if (beats):
            # Calculate whether or not beat should be considered
            if (time.time()+(BEAT_DELAY*0.15)-(beats+1)*BEAT_DELAY >= initt):
                if (not b):
                    if (float(cspb)/tspb >= 0.8):
                        print("EIGHTH NOTE")
                        rec = True
                        o1 = int(round(f2n(find_max_mode(samp))))
                        a1 = notes[-1].pitch
                        a2 = o1
                        # Extend previous note if previous note is eighth note and current note is same pitch
                        if (rec and a1 == a2 and not notes[-1].value % 2):
                            notes[-1].value += 2;
                        # If no notes have been added, or if previous note is not eighth note, add current note
                        else:
                            note = Note()
                            note.pitch = o1
                            note.value = 2
                            notes.append(note)
                    elif (float(cspb)/tspb >= 0.35):
                        print("SIXTEENTH NOTE + REST")
                        rec = True
                        o1 = int(round(f2n(find_max_mode(samp))))
                        a1 = notes[-1].pitch
                        a2 = o1
                        # Extend previous note if previous note is eighth note and current note is same pitch, and append sixteenth rest
                        if (rec and a1 == a2 and not notes[-1].value % 2):
                            notes[-1].value += 1;
                            note = Note()
                            note.pitch = 0
                            note.value = 1
                            notes.append(note)
                        # If no notes have been added, or if previous note is not eighth note, add current note, and append sixteenth rest
                        else:
                            note = Note()
                            note.pitch = o1
                            note.value = 1
                            notes.append(note)
                            note = Note()
                            note.pitch = 0
                            note.value = 1
                            notes.append(note)
                    else:
                        print("...")
                        if (rec):
                            # Extend previous rest if previous note is a rest
                            a1 = notes[-1].pitch
                            if (not a1):
                                notes[-1].value += 2
                            # If previous note is not a rest, append new rest
                            else:
                                note = Note()
                                note.pitch = 0
                                note.value = 2
                                notes.append(note)
                    samp = []
                    b = 1
            else:
                b = 0

for i in notes:
    print("%s, %d" % (i.value, i.pitch))

WHITE = 255, 255, 255
BLACK = 0, 0, 0

WIDTH = 800
HEIGHT = 800
FPS = 60


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("sheetmusicmaker")
clock = pygame.time.Clock()

font_name = pygame.font.match_font('arial')
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)



screen.fill(WHITE)   

NOTE_NAMES = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]

def nn(n):
    return NOTE_NAMES[n%12] + 7*int(n/12-1)

time_duration = 0
x_pos = 15
y_pos = HEIGHT / 4
c5_height = 70
over = True
running = True
gs = pygame.image.load("grandstaff.png").convert_alpha()
screen.blit(gs, [0, 0])
notespassed = 0
for i in range(1, len(notes)):
    notespassed += notes[i].value
    element = notes[i]
    if element.pitch == 0:
        if element.value == 1:
            image = pygame.image.load("sixteenthrest.png").convert_alpha()
            image = pygame.transform.scale(image,(50,50))
            y_pos = c5_height + 60
            print('1')
        if element.value == 2:
            image = pygame.image.load("eighthrest.png").convert_alpha()
            image = pygame.transform.scale(image,(50,50))
            y_pos = c5_height + 60
            print('2')
        if element.value == 3:
            image = pygame.image.load("dottedeighthrest.png").convert_alpha()
            image = pygame.transform.scale(image,(50,50))
            y_pos = c5_height + 60
            x_pos += 30
            print('3')
        if element.value == 4:
            image = pygame.image.load("quarterrest.png").convert_alpha()
            image = pygame.transform.scale(image,(75,75))
            y_pos = c5_height + 40
            print('4')
        if element.value == 6:
            image = pygame.image.load("dottedquarterrest.png").convert_alpha()
            image = pygame.transform.scale(image,(75,75))
            y_pos = c5_height + 40
            print('5')
        if element.value == 8:
            image = pygame.image.load("halfrest.png").convert_alpha()
            image = pygame.transform.scale(image,(55,10))
            y_pos = c5_height + 70
            
            print('6')
        x_pos += 60
        screen.blit(image, [x_pos, y_pos])
        print(str(y_pos))
        time_duration += element.value*0.25
    else:
        rotation = False
        if element.pitch >= 71:
               rotation = True
        if element.value == 1:
            image = pygame.image.load("sixteenthnotes.png").convert_alpha()
            image = pygame.transform.scale(image,(75,75))
            y_pos = c5_height + 10 - (nn(element.pitch)-35)*9 + (48 if rotation else 0)
        if element.value == 2:
            image = pygame.image.load("eighthnotes.png").convert_alpha()
            image = pygame.transform.scale(image,(85,85))
            y_pos = c5_height - (nn(element.pitch)-35)*9 + (60 if rotation else 0)
        if element.value == 3:
            image = pygame.image.load("dottedeighthnote.png").convert_alpha()
            image = pygame.transform.scale(image,(85,85))
            y_pos = c5_height - 5 - (nn(element.pitch)-35)*9 + (80 if rotation else 0)
        if element.value == 4:
            image = pygame.image.load("quarternotes.png").convert_alpha()
            image = pygame.transform.scale(image,(75,75))
            y_pos = c5_height + 8 - (nn(element.pitch)-35)*9 + (50 if rotation else 0)
        if element.value == 6:
            image = pygame.image.load("dottedquarternote.png").convert_alpha()
            image = pygame.transform.scale(image,(75,110))
            y_pos = c5_height - 15 - (nn(element.pitch)-35)*9 + (60 if rotation else 0)
        if element.value == 8:
            image = pygame.image.load("halfnotes.png").convert_alpha()
            image = pygame.transform.scale(image,(75,75))
            y_pos = c5_height + 8 - (nn(element.pitch)-35)*9 + (60 if rotation else 0)
        print(str(nn(72)))
        if rotation:
            image = pygame.transform.rotate(image, 180)
        x_pos += 60
        if (notespassed >= 16):
            x_pos += 60
            y_pos = 100
            image = pygame.image.load("barline.png").convert_alpha()
            notespassed -= 16
        screen.blit(image, [x_pos, y_pos])
        time_duration += element.value*0.25

while running:
    if over:
        over = False
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False



    pygame.display.flip()


pygame.quit()

