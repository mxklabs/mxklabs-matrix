This is some hacked-together code to set a matrix display attached to a Raspberry PI
from your main desktop computer. It is not production-level code.

# On a desktop machine

## Software prerequisites

* Tested on Windows 10 and Ubuntu 22.
* Create a venv for this project and install this project's requirements.txt in there.

## Run

In your venv, call:
```
python /path/to/project/mxklabs-matrix/desktopgui/desktop.py
```

# On the device

## Hardware requirements

* Raspberry PI 3 model B (other boards untested).
* Waveshare RGB-Matrix-P3-64x64 matrix displays wired up according to [this wiring guide](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/wiring.md).

## Software prerequisites

* Fresh Raspberry Pi OS.
* Create a venv for this project and install this project's requirements.txt in there.
* Download and install [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix/) (both c++ libraries and the Python bindings, the latter preferably in the venv).
  * We use a custom version of this repo because of our hardware config, see https://github.com/mxklabs/rpi-rgb-led-matrix/tree/MorkPixelMapper. 
* You may wish to dedicate some of your cores to this project by adding, e.g., `isolcpus=2,3` to `/boot/cmdline.txt`.

## Run

Note: 

* You need to run as sudo priviledges to control GPIO 18, which is used for PWMing.
* You need to pass in the full path of `device.py` (there is a bug somewhere that means Pathlib won't see a directory exists).
* You can configure CPU affinity for two of the main processing threads (flash web server and the matrix updater) in the `config.json` file.
So your command should look something like this.
```
sudo /path/to/venv/bin/python /path/to/project/mxklabs-matrix/desktopgui/device.py
```