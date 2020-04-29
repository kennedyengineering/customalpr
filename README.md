# customALPR

A universal license plate detection program

## Getting Started

customALPR uses OpenALPR for license plate detection and OCR. It then stores the license plate information
in a SQLite database (database/database.db) and an image of the license plate (database/Images). customALPR can run in headless mode, or GUI mode, depending on
how the configuration file is set. customALPR is capable of handling several cameras in one instance, with each camera running on a 
separate thread, and all the data stored in one database.

### Dependencies

customalpr is tested to work under Python 3.x. See the requirements via the following command:

```
cat requirements.txt
```

### Installing

```
python3 -v venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Installing OpenALPR

Follow the "Easy Way (Ubuntu 14.04+)" installation tutorial. Not "The Easiest Way" installation tutorial. That will not work. [link](https://github.com/openalpr/openalpr/wiki/Compilation-instructions-(Ubuntu-Linux))

If there are any issues this thread is helpful. [link](https://github.com/openalpr/openalpr/issues/660)

## Configuration

CustomALPR has a config file (config.yml) that is used for adding cameras, establishing search zones, and toggling between GUI/no-GUI, and GUI screen size.

The file is constructed, by default as shown:
```
cameraAddresses:
	- example_camera_name:
		- url: rtsp://example.url/Streaming/channels/101/
		- aoi:
			- search_zone_1:
				- X: 100
				- Y: 100
				- W: 100
				- H: 100
			- search_zone_2:
				- X: 200
				- Y: 200
				- W: 100
				- H: 100

GUItoggle: true
GUIresolutionX: 800
GUIresolutionY: 600
```

Breaking it down:

*cameraAddresses* - the list that contains camera definitions <br />
*example_camera_name* - name of the camera (can change) <br />
*url* - the source of the video feed. Can be url of an IP camera or a path to a video. Can be anything opencv.VideoCapture can open. <br />
*aoi* - area of interest. CustomALPR will only search for licenseplates within the bounds of this rectangle. Use the aoi_finder.py utility to find the values. <br />
*X*,*Y*,*W*,*H* - rectangle definiton. Defines the area concerning the aoi. aoi_finder.py returns values in this order. <br />
*GUItoggle* - self explanatory <br />
*GUIresolutionX* - size of GUI screen's width in pixels <br />
*GUIresolutionY* - size of GUI screen's height in pixels <br />

### Starting CustomALPR

Simply run main.py with python3
```
python3 main.py
```

## Authors

* **Braedan Kennedy** - *Initial work* - [kennedyengineering](https://github.com/kennedyengineering)

## Acknowledgments
This project builds heavily upon the work done by OpenAlpr. [link](https://github.com/openalpr/openalpr)

Thanks to Adrian at PyImageSearch for the optimized webcam class. [link](https://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/)
