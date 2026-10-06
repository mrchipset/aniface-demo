import mediapipe as mp, numpy as np
from PIL import Image, ImageDraw, ImageFont

PHOTO = r"<HOME>\Downloads\photo.jpg"
img = Image.open(PHOTO).convert("RGB")
W,H = img.size
arr = np.array(img)

fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                     refine_landmarks=False, min_detection_confidence=0.3)
res = fm.process(arr)
print("faces:", len(res.multi_face_landmarks) if res.multi_face_landmarks else 0)
lm = res.multi_face_landmarks[0].landmark
pts = np.array([[p.x*W, p.y*H] for p in lm])
np.save("mp_landmarks.npy", pts)
print("landmarks:", pts.shape)
print("x %.0f..%.0f  y %.0f..%.0f" % (pts[:,0].min(),pts[:,0].max(),pts[:,1].min(),pts[:,1].max()))

CAND = [
 ("j0",0,127),("j2",2,234),("chin",8,152),("j14",14,454),("j16",16,356),
 ("bR17",17,70),("bR19",19,105),("bR21",21,107),
 ("bL22",22,336),("bL24",24,334),("bL26",26,300),
 ("br27",27,168),("nose30",30,4),("nL31",31,129),("nR35",35,358),
 ("eR36",36,33),("eR39",39,133),("eL42",42,362),("eL45",45,263),
 ("eR37",37,159),("eR41",41,145),("eL44",44,386),("eL46",46,374),
 ("mR48",48,61),("mL54",54,291),("uL51",51,13),("lL57",57,14),
 ("oL62",62,17),("oL66",66,0),
]
im2 = img.copy(); d = ImageDraw.Draw(im2)
cols = [(255,0,0),(0,140,255),(0,180,0),(255,140,0)]
for k,(name,ict,mpi) in enumerate(CAND):
    x,y = pts[mpi]
    c = cols[k % 4]
    d.ellipse([x-6,y-6,x+6,y+6], outline=c, width=3)
    d.text((x+8,y-10), str(ict), fill=c)
im2.save("lm_check.png")
print("saved lm_check.png")
for name,ict,mpi in CAND:
    print("  %-7s ict#%-3d MP[%3d] -> (%.0f,%.0f)" % (name,ict,mpi,pts[mpi][0],pts[mpi][1]))
