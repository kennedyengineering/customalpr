import cv2
import sys
# types: BOOSTING, MIL, KCF, TLD, MED
tracker_type = 'KCF'

# tracker = cv2.Tracker_create(tracker_type)
tracker = cv2.TrackerKCF_create()

cam = cv2.VideoCapture(0)
ret, frame = cam.read()
while not ret:              # wait for camera to open
    ret, frame = cam.read()

for _ in range(30):         # let camera adjust
    ret, frame = cam.read()

# bbox = (287, 23, 86, 320)
bbox = cv2.selectROI(frame, False)
cv2.destroyAllWindows()

ok = tracker.init(frame, bbox)

def overlap(a, b):
    #x,y,w,h

    x = a[0]
    y = a[1]
    w = a[2]
    h = a[3]

    upperleft1 = (x, y)
    upperright1 = (x+w, y)
    lowerleft1 = (x, y+h)
    lowerright1 = (x+w, y+h)

    x = b[0]
    y = b[1]
    w = b[2]
    h = b[3]

    upperleft2 = (x, y)
    upperright2 = (x+w, y)
    lowerleft2 = (x, y+h)
    lowerright2 = (x+w, y+h)

    # test if any point from first rect is inside second rect
    # first rect -- 1
    # second recr -- 2

    #check top left X
    topLeftX = False 
    if (upperleft1[0] < upperright2[0]):
        if (upperleft1[0] > upperleft2[0]):
            topLeftX = True

    topLeftY = False
    if (upperleft1[1] > upperleft2[1]):
        if (upperleft1[1] < lowerleft2[1]):
            topLeftY = True

    topLeft = False
    if topLeftY and topLeftX:
        topLeft = True
    #WORKS!

    #check top right XY
    topRightX = False
    if (upperright1[0] < upperright2[0]):
	if (upperright1[0] > upperleft2[0]):
		topRightX = True
    
    topRightY = False
    if (upperright1[1] > upperleft2[1]):
	if (upperright1[1] < lowerleft2[1]):
		topRightY = True

    topRight = False
    if topRightY and topRightX:
	topRight = True
	


    #check bottom left XY
    bottomLeftX = False
    if (lowerleft1[0] < upperright2[0]):
	if (lowerleft1[0] > upperleft2[0]):
		bottomLeftX = True

    bottomLeftY = False
    if (lowerleft1[1] > upperleft2[1]):
	if (lowerleft1[1] < lowerleft2[1]):
    		bottomLeftY = True

    bottomLeft = False
    if bottomLeftY and bottomLeftX:
	bottomLeft = True



    #check bottom right XY
    bottomRightX = False
    if (lowerright1[0] < upperright2[0]):
	if (lowerright1[0] > upperleft2[0]):
		bottomRightX = True
    
    bottomRightY = False
    if (lowerright1[1] > upperleft2[1]):
	if (lowerright1[1] < lowerleft2[1]):
		bottomRightY = True

    bottomRight = False
    if bottomRightX and bottomRightY:
	bottomRight = True

	
    if bottomRight or bottomLeft or topLeft or topRight:
	return True
    else:
	return False


testRect = {"x":300, "y":300, "w":100, "h":50}

while True:
    ret, frame = cam.read()

    timer = cv2.getTickCount()

    ok, bbox = tracker.update(frame)

    #testRect["x"] += 1
    #testRect["y"] += 1
    cv2.rectangle(frame, (testRect["x"], testRect["y"]), (testRect["x"]+testRect["w"], testRect["y"]+testRect["h"]), (0,255,0), 2, 1)

    fps = cv2.getTickFrequency()/(cv2.getTickCount()-timer)

    if ok:
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        #cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
        modRect = (testRect['x'], testRect['y'], testRect['w'], testRect['h'])
        moddedRect = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
        cv2.rectangle(frame, moddedRect, (255,0,0), 2, 1)
        print(overlap(modRect, moddedRect))
    else:
        cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, .75, (0,0,255), 2)

    cv2.putText(frame, tracker_type + " Tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)
    cv2.putText(frame, "FPS : " + str(int(fps)), (100,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)

    cv2.imshow("Tracking", frame)

    k = cv2.waitKey(1) & 0xff  # esc key
    if k == 27:
        break
