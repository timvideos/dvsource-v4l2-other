#! /usr/bin/python
#
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:
#

"""
dvsource-v4l2-other - Video4Linux2 source for DVswitch which supports any device.
"""

import argparse
import atexit
import os
import tempfile
import time
import subprocess
import shutil

subprocess.DEVNULL = file(os.devnull, "rw+")


###############################################################################
# Argument parsing
###############################################################################

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-d", "--device", default="/dev/video0",
    help="Video4Linux device to read the input from.")
parser.add_argument(
    "-c", "--caps", default="",
    help="gstreamer caps to force v4l2src device to use.")

parser.add_argument(
    "-s", "--system", default="pal", choices=["ntsc", "pal"],
    help="Specify the video system to use.This must match the system used by DVswitch.")
parser.add_argument(
    "-a", "--aspect", default="4:3", choices=["4:3", "16:9"],
    help="Choose DV output aspect ratio.")
parser.add_argument(
    "-t", "--timeout", type=int, default=10,
    help="How long to wait when terminating subprocess before killing.")

parser.add_argument(
    "-r", "--rate", default="48000", choices=["48000", "44100", "32000"],
    help="Specify the sample rate, in Hz. **Only 48000kHz is supported.**")


fake_types = {
    None: 0,
    "": 0,
    "smpte": 0,
    "snow": 1,
    "black": 2,
    "white": 3,
    "red": 4,
    "green": 5,
    "blue": 6,
    "checkers-1": 7,
    "checkers-2": 8,
    "checkers-4": 9,
    "checkers-8": 10,
    "circular": 11,
    "blink": 12,
    "smpte": 13,
    "zone-plate": 14,
    "gamut": 15,
    "chroma-zone-plate": 16,
    "solid-color": 17,
    "ball": 18,
    "smpte": 19,
    "bar": 20,
    }
parser.add_argument(
    "-n", "--fake", choices=fake_types.keys(),
    help="Use a fake source rather then a real V4L2 device.")

parser.add_argument(
    "-v", "--verbose", action="store_true",
    help="Increase output verbosity")

parser.add_argument(
    "-x", "--display", action="store_true",
    help="Display the incoming video locally.")

parser.add_argument(
    "-3", "--c3voc", type=int, default=-1,
    help="Connecting to a C3 VOC's custom dvswitch version with given source ID.")

###############################################################################
# dvswitch arguments and .dvswitchrc parsing
###############################################################################

def parse_dvswitchrc(configfile):
    r = {}
    for line in file(configfile, "r").readlines():
        cmt = line.find('#')
        if cmt > 0:
            line = line[cmt:]

        line = line.strip()
        if not line:
            continue

        key, value = line.split('=', 1)
        r[key] = value
    return r


def get_dvswitchrc():
    import shlex
    from os import path
    configs = [path.expanduser("~"), ".", "/etc"]

    actual_config = {}
    for dirname in configs:
        configfile = path.join(dirname, ".dvswitchrc")
        if path.exists(configfile):
            actual_config.update(parse_dvswitchrc(configfile))

    if actual_config.get("MIXER_HOST", None) == "0.0.0.0":
        actual_config["MIXER_HOST"] = "127.0.0.1"

    return actual_config

config = get_dvswitchrc()
# dvswitch arguments
parser.add_argument(
    "-h", "--host", 
    help=(""
        "Specify the network address on which DVswitch is listening. The host"
        " address may be specified by name or as an IPv4 or IPv6 literal."),
    default = config.get("MIXER_HOST", None),
    required = config.get("MIXER_HOST", None) == None,
    )
parser.add_argument(
    "-p", "--port",
    help=(""
        "Specify the network address on which DVswitch is listening. The host"
        " address may be specified by name or as an IPv4 or IPv6 literal."),
    default = config.get("MIXER_PORT", None),
    required = config.get("MIXER_PORT", None) == None,
    )

###############################################################################

parser.add_argument(
    "--help", action='help',
    help="show this help message and exit")

###############################################################################
# Code to check dependencies
###############################################################################
def check_command(name, package=None):
    try:
        output = subprocess.check_output(["which", name])
        if args.verbose:
          print "Using", name, "found at", output.strip()
    except subprocess.CalledProcessError, e:
        print "Unable to find required command:", name
        if package:
            print "Please try 'sudo apt-get install %s'" % package
        raise

def check_gst_module(name, package=None, extra_help=None):
    try:
        subprocess.check_call(["gst-inspect-1.0", name], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError, e:
        print "Unable to find required gstreamer module", name
        if package:
            print "Please try 'sudo apt-get install %s'" % package
        if extra_help:
            print extra_help
        raise

###############################################################################
# Code to which actually does the work
###############################################################################

def launch_gstreamer():
    if args.c3voc >= 0:
        dvswitchsink_extra = " c3voc-mode=1 c3voc-source-id=%i " % args.c3voc
    else:
        dvswitchsink_extra = ""

    if args.caps:
        args.caps += " ! "

    cmd = ("gst-launch-1.0" +
        " " +
        {True: "-v",
         False: ""
        }[args.verbose] +
        " " +
        # Video Pipeline --------------------
        # -----------------------------------
        {True:
            # Read the v4l2 input and decode it if it's a mjpeg input
            "v4l2src device=%s ! " % args.device +
            args.caps +
            "decodebin ! ",
         False:
          "videotestsrc is-live=true pattern=%s !" % fake_types[args.fake],
        }[args.fake == None] +
        " " +
        # Allow at most 1ms of data to be in the buffer, 2=GST_QUEUE_LEAK_DOWNSTREAM
        "queue leaky=downstream max-size-buffers=1 ! " +
        " " +
        # Convert to 4:3 format by adding borders if needed
        {"4:3":
            # Convert to 4:3 format by adding borders if needed
            "videoscale add-borders=1 ! video/x-raw,width=1024,height=768,pixel-aspect-ratio=\(fraction\)1/1 !",
         "16:9":
            # Convert to 16:9 format by adding borders if needed
            "videoscale add-borders=1 ! video/x-raw,width=1280,height=720,pixel-aspect-ratio=\(fraction\)1/1 !",
        }[args.aspect] +
        " " +
        # Pixel aspect ratio conversion is a bit hairy, see the following links for more information.
        # http://forum.doom9.org/showthread.php?t=111102
        # http://www.sciencemedianetwork.org/wiki/Tutorials/Video/Pixel_Aspect_Ratio
        {"ntsc-4:3": 
            # Convert to 4:3 with non-square pixels (was 10.0/11 ~= 0.91, now 8.0/9 ~= 0.88)
            "videoscale ! video/x-raw,width=720,height=480,pixel-aspect-ratio=\(fraction\)8/9 !",
         "ntsc-16:9": 
            # Convert to 16:9 with non-square pixels (was 40.0/33 ~= 1.21, now 32.0/27 ~= 1.19)
            "videoscale ! video/x-raw,width=720,height=480,pixel-aspect-ratio=\(fraction\)32/27 !",
         "pal-4:3":
            # Convert to 4:3 with non-square pixels (was 59.0/54 ~= 1.09 == ITU-PAR, now 16.0/15 ~= 1.07 == NLE-PAR used by Final Cut / Adobe)
            # I420 == works, Y41B == works, Y42B == not working
            "videoscale ! video/x-raw,width=720,height=576,pixel-aspect-ratio=\(fraction\)16/15 !",
         "pal-16:9":
            # Convert to 16:9 with non-square pixels (was 118.0/81 ~= 1.46 == anamorphic 'ITU', now 64.0/45 ~= 1.42 == anamorphic 'NLE')
            "videoscale ! video/x-raw,width=720,height=576,pixel-aspect-ratio=\(fraction\)64/45 !",
        }["%s-%s" % (args.system, args.aspect)] +
        " " +
        {"ntsc": 
            # Convert the framerate to 30fps
            "videorate ! video/x-raw,framerate=\(fraction\)30000/1001 !",
         "pal":
            # Convert the framerate to 25fps
            "videorate ! video/x-raw,framerate=\(fraction\)25/1 !",
        }[args.system] +
        " " +
        # Convert to color space needed by dvswitch
        # For PAL, either I420 or Y41B works.
        # For NTSC, only Y41B seems to work.
        # Y42B doesn't seem supported by dvswitch at all.
        "videoconvert ! video/x-raw,format=\(string\)Y41B !" +
        " " +
        ["", "tee name=t ! "][args.display] +
        " " +
        "queue leaky=downstream max-size-buffers=1 ! " +
        " " +
        # Convert to DV format
        "videoconvert ! avenc_dvvideo ! avmux_dv name=dvmux !" +
        " " +
        # Output to dvswitch
        "dvswitchsink host=%s port=%s %s" % (args.host, args.port, dvswitchsink_extra) +
        " " +
        # -----------------------------------
        # Audio Pipeline --------------------
        # -----------------------------------
        " " +
        # Generate a dummy audio signal
        # 2 channels, 16-bit Linear PCM at 48 kHz
        # 2 channels, 16-bit Linear PCM at 44.1 kHz
        # 4 channels, 12-bit nonlinear PCM channels at 32 kHz (Not supported - gstreamer doesn't support 12-bit nonlinear)
        "audiotestsrc is-live=true wave=sine freq=200 ! audio/x-raw,channels=2,rate=%s,depth=16 ! queue ! dvmux." % args.rate +
        " " +
        # -----------------------------------
        # Local Display ---------------------
        # -----------------------------------
        " " +
        ["", "t. ! queue max-size-buffers=1 leaky=downstream ! videoconvert ! xvimagesink"][args.display]
        )

    cmdargs = {}
    if args.verbose:
        print "Running the gstreamer conversion command of"
        print "   ", cmd
    else:
        cmdargs["stdout"] = subprocess.DEVNULL

    return subprocess.Popen(cmd, shell=True, **cmdargs)


###############################################################################
# Main function
###############################################################################
def main():
    # Check that gstreamer cmd line tools are installed
    check_command("gst-inspect-1.0", "gstreamer1.0-tools")
    check_command("gst-launch-1.0", "gstreamer1.0-tools")
    # Check if the gstreamer modules are installed
    check_gst_module("v4l2src", "gstreamer1.0-plugins-good")
    check_gst_module("decodebin", "gstreamer1.0-plugins-base")

    check_gst_module("videotestsrc", "gstreamer1.0-plugins-base")

    check_gst_module("videoscale", "gstreamer1.0-plugins-base")
    check_gst_module("videorate", "gstreamer1.0-plugins-base")

    check_gst_module("queue", "libgstreamer1.0-0")
    check_gst_module("tee", "libgstreamer1.0-0")

    check_gst_module("videoconvert", "gstreamer1.0-libav")
    check_gst_module("avenc_dvvideo", "gstreamer1.0-libav")
    check_gst_module("avmux_dv", "gstreamer1.0-libav")
    check_gst_module("dvswitchsink", "gstreamer1.0-dvswitch", """
If your distro doesn't ship the gstreamer1.0-dvswitch package you
can find out more information in the README.md file or at
https://github.com/timvideos/dvsource-v4l2-other#installing-the-gstreamer-dvswitch-plugin
""")

    check_gst_module("audiotestsrc", "gstreamer1.0-plugins-base")

    check_gst_module("xvimagesink", "gstreamer1.0-plugins-base")

    # Check the input arguments make sense.
    if args.rate != "48000":
        raise SystemError("Only a --rate of 48000 is supported.")

    # Launch the sub-commands
    gst = launch_gstreamer()

    try:
        while True:
            if gst.poll() != None:
                raise OSError("gst-launch command terminated!")

            # FIXME: Add some type of monitoring of CPU usage here...
            if args.verbose:
                print "gst-launch happily running!"

            time.sleep(1.0)
    except KeyboardInterrupt, e:
        pass
    finally:
        exitstart = time.time()

        try:
            if args.verbose:
                print "Terminating gst-launch"
            gst.terminate()
        except Exception, e:
            print "Error terminating gst-launch", e

        while True:
            if gst.poll() != None:
                break

            if args.verbose:
                print "Waiting for gst-launch to terminate"
            time.sleep(1)

            if time.time() - exitstart > args.timeout:
                print "Timeout waiting for gst-launch",
                print "to terminate, killing."

		try:
		    gst.kill()
		except Exception, e:
		    print "Error killing gst-launch", e


args = None
if __name__ == "__main__":
    args = parser.parse_args()
    main()
