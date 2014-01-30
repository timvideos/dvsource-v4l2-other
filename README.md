# dvsource-v4l2-other

A source for DVswitch which supports any Video4Linux 2 device.

## Quick Start

```
dvswitch --host=localhost --port=2000 &
./dvsource-v4l2-other --device=/dev/video0 --host=localhost --port=2000
```

## Dependencies

 * gstreamer-0.10 (including, base, good and ffmpeg plugins)
 * gst-plugins-dvswitch -- https://github.com/timvideos/gst-plugins-dvswitch

### Installing on Debian and Ubuntu

#### Dependencies
The following packages are needed;

 * gstreamer0.10-tools
 * gstreamer0.10-plugins-good
 * gstreamer0.10-plugins-base
 * gstreamer0.10-ffmpeg
 * libgstreamer0.10-0
 * gstreamer0.10-dvswitch
   * Download from https://github.com/timvideos/gst-plugins-dvswitch

##### Installing the dependencies
```
sudo apt-get install \
  gstreamer0.10-tools \
  gstreamer0.10-plugins-good \
  gstreamer0.10-plugins-base \
  gstreamer0.10-ffmpeg \
  libgstreamer0.10-0
```

##### Installing the gstreamer dvswitch plugin

If your distro has gstreamer0.10-dvswitch
```
sudo apt-get install \
  gstreamer0.10-dvswitch
```

Else, build the gstreamer0.10-dvswitch package yourself
```
git clone git://github.com/timvideos/gst-plugins-dvswitch.git
cd gst-plugins-dvswitch
dpkg-checkbuilddeps
# Install any missing build dependencies
dpkg-buildpackage -b
dpkg --install ../gstreamer0.10-dvswitch*.deb
```

# Usage

```
usage: dvsource-v4l2-other [-d DEVICE] [-c CAPS] [-f {ntsc,pal}]
                           [-a {4:3,16:9}] [-t TIMEOUT]
                           [-n {...}]
                           [-v] [-x] [-h HOST] [-p PORT] [--help]

optional arguments:
  -d DEVICE, --device DEVICE
                        Video4Linux device to read the input from.
  -c CAPS, --caps CAPS  gstreamer caps to force v4l2src device to use.
  -f {ntsc,pal}, --format {ntsc,pal}
                        Choose DV output format.
  -a {4:3,16:9}, --aspect {4:3,16:9}
                        Choose DV output aspect ratio.
  -t TIMEOUT, --timeout TIMEOUT
                        How long to wait when terminating subprocess before
                        killing.
  -n {blue,checkers-1,checkers-2,bar,checkers-4,chroma-zone-plate,checkers-8,ball,snow,solid-color,blink,smpte,gamut,black,green,zone-plate,white,red,circular}, --fake {blue,checkers-1,checkers-2,bar,checkers-4,chroma-zone-plate,checkers-8,ball,snow,solid-color,blink,smpte,gamut,black,green,zone-plate,white,red,circular}
                        Use a fake source rather then a real V4L2 device.
  -v, --verbose         Increase output verbosity
  -x, --display         Display the incoming video locally.
  -h HOST, --host HOST  Specify the network address on which DVswitch is
                        listening. The host address may be specified by name
                        or as an IPv4 or IPv6 literal.
  -p PORT, --port PORT  Specify the network address on which DVswitch is
                        listening. The host address may be specified by name
                        or as an IPv4 or IPv6 literal.
  --help                show this help message and exit
```
