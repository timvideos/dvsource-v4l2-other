# dvsource-v4l2-other

A source for DVswitch which supports any Video4Linux 2 device.

## Quick Start

```
dvswitch --host=localhost --port=2000 &
./dvsource-v4l2-other --device=/dev/video0 --host=localhost --port=2000
```

## Dependencies

 * gstreamer-1.2.4 (including, base, good and libav plugins)
 * gst-plugins-dvswitch -- https://github.com/timvideos/gst-plugins-dvswitch

### Installing on Debian and Ubuntu

#### Dependencies
The following packages are needed;

 * gstreamer1.0-tools
 * gstreamer1.0-plugins-good
 * gstreamer1.0-plugins-base
 * gstreamer1.0-libav
 * libgstreamer1.0-0
 * gstreamer1.0-dvswitch
   * Download from https://github.com/timvideos/gst-plugins-dvswitch

##### Installing the dependencies
```
sudo apt-get install \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-base \
  gstreamer1.0-libav \
  libgstreamer1.0-0
```

##### Installing the gstreamer dvswitch plugin

If your distro has gstreamer1.0-dvswitch
```
sudo apt-get install gstreamer1.0-dvswitch
```

Else, install from the ppa
```
sudo add-apt-repository ppa:aps-sids/ppa
sudo apt-get update
sudo apt-get install gstreamer1.0-dvswitch
```

Else, build the gstreamer1.0-dvswitch package yourself
```
git clone git://github.com/timvideos/gst-plugins-dvswitch.git
cd gst-plugins-dvswitch
dpkg-checkbuilddeps
# Install any missing build dependencies
dpkg-buildpackage -b
dpkg --install ../gstreamer1.0-dvswitch*.deb
```

# Usage

```
usage: dvsource-v4l2-other [-d DEVICE] [-c CAPS] [-s {ntsc,pal}]
                           [-a {4:3,16:9}] [-t TIMEOUT]
                           [-r {48000,44100,32000}]
                           [-n TYPE]
                           [-v] [-x] [-h HOST] [-p PORT] [--help]

optional arguments:
  -d DEVICE, --device DEVICE
                        Video4Linux device to read the input from.
  -c CAPS, --caps CAPS  gstreamer caps to force v4l2src device to use.
  -s {ntsc,pal}, --system {ntsc,pal}
                        Specify the video system to use.This must match the
                        system used by DVswitch.
  -a {4:3,16:9}, --aspect {4:3,16:9}
                        Choose DV output aspect ratio.
  -t TIMEOUT, --timeout TIMEOUT
                        How long to wait when terminating subprocess before
                        killing.
  -r {48000,44100,32000}, --rate {48000,44100,32000}
                        Specify the sample rate, in Hz. **Only 48000kHz is
                        supported.**
  -n TYPE, --fake TYPE
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
