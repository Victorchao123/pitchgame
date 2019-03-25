class Note:
    pitch = 0 # 0 if rest, otherwise semitone number (C4=60, C#4=61, D4=62, etc...)
    value = 1
a = Note()
b = Note()
c = Note()
d = Note()
e = Note()
f = Note()
g = Note()
h = Note()
a.value = 1; a.pitch = 0
b.value = 8; b.pitch = 70
c.value = 4; c.pitch = 0
d.value = 6; d.pitch = 74
e.value = 16; e.pitch = 0
f.value = 1; f.pitch = 93
g.value = 1; g.pitch = 0
h.value = 1; h.pitch = 94
notes = [a,b,c,d,e,f,g,h]
for i in notes:
    print(i.value)