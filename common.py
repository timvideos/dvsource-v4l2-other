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


class dvsource_common(object):

    @staticmethod
    def get_arguments():
        # We have to disable help as we want -h to be used for host.
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            "--help", action='help',
            help="show this help message and exit")

        parser.add_argument(
            "-v", "--verbose", action="store_true",
            help="Increase output verbosity")

        # Control the DV format we will send to dvswitch
        parser.add_argument(
            "-f", "--format", default="ntsc", choices=["ntsc", "pal"],
            help="Choose DV output format.")
        parser.add_argument(
            "-a", "--aspect", default="4:3", choices=["4:3", "16:9"],
            help="Choose DV output aspect ratio.")

        parser.add_argument(
            "-x", "--display", action="store_true",
            help="Display the incoming video locally.")

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


    @staticmethod
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

    @staticmethod
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

    ###############################################################################
    # Code to check dependencies
    ###############################################################################
    @staticmethod
    def check_command(name):
        try:
            output = subprocess.check_output(["which", name])
            if args.verbose:
              print "Using", name, "found at", output.strip()
        except subprocess.CalledProcessError, e:
            print "Unable to find required command:", name
            raise

    @staticmethod
    def check_gst_module(name):
        try:
            subprocess.check_call(["gst-inspect-0.10", name], stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError, e:
            print "Unable to find required gstreamer module", name
            raise

###############################################################################
# Code to which actually does the work
###############################################################################

    def get_gstreamer_pipeline(args):
        cmd = (
            # Allow at most 1ms of data to be in the buffer, 2=GST_QUEUE_LEAK_DOWNSTREAM
            "queue leaky=downstream max-size-buffers=1 ! " +
            " " +
            # Convert to 4:3 format by adding borders if needed
            {"4:3":
                # Convert to 4:3 format by adding borders if needed
                "videoscale add-borders=1 ! video/x-raw-yuv,width=1024,height=768,pixel-aspect-ratio=\(fraction\)1/1 !",
             "16:9":
                # Convert to 16:9 format by adding borders if needed
                "videoscale add-borders=1 ! video/x-raw-yuv,width=1280,height=720,pixel-aspect-ratio=\(fraction\)1/1 !",
            }[args.aspect] +
            " " +
            {"ntsc-4:3": 
                # Convert to 4:3 with non-square pixels
                "videoscale ! video/x-raw-yuv,width=720,height=480,pixel-aspect-ratio=\(fraction\)10/11 !",
             "ntsc-16:9": 
                # Convert to 4:3 with non-square pixels
                "videoscale ! video/x-raw-yuv,width=720,height=480,pixel-aspect-ratio=\(fraction\)40/33 !",
             "pal-4:3":
                # Convert to 4:3 with non-square pixels
                "videoscale ! video/x-raw-yuv,width=720,height=576,pixel-aspect-ratio=\(fraction\)59/54 !",
             "pal-4:3":
                # Convert to 4:3 with non-square pixels
                "videoscale ! video/x-raw-yuv,width=720,height=576,pixel-aspect-ratio=\(fraction\)118/81 !",
            }["%s-%s" % (args.format, args.aspect)] +
            " " +
            {"ntsc": 
                # Convert the framerate to 30fps
                "videorate ! video/x-raw-yuv,framerate=\(fraction\)30000/1001 !",
             "pal":
                # Convert the framerate to 25fps
                "videorate ! video/x-raw-yuv,framerate=\(fraction\)25/1 !",
            }[args.format] +
            " " +
            ["", "tee name=t ! "][args.display] +
            " " +
            "queue leaky=downstream max-size-buffers=1 ! " +
            " " +
            # Convert to DV format
            "ffmpegcolorspace ! ffenc_dvvideo ! ffmux_dv !" +
            " " +
            # Output to the fifo
            "dvswitchsink host=%s port=%s" % (args.host, args.port) +
            " " +
            ["", "t.! queue max-size-buffers=1 leaky=downstream ! ffmpegcolorspace ! xvimagesink"][args.display]
            )

###############################################################################
# Main function
###############################################################################
def main():
    # Check that gstreamer stuff is installed
    check_command("gst-inspect-0.10")
    check_command("gst-launch-0.10")
    check_gst_module("v4l2src")
    check_gst_module("decodebin2")
    check_gst_module("videoscale")
    check_gst_module("videorate")
    check_gst_module("ffmpegcolorspace")
    check_gst_module("ffenc_dvvideo")
    check_gst_module("ffmux_dv")
    check_gst_module("filesink")
    check_gst_module("dvswitchsink")

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
    finally:
        exitstart = time.time()

        # To not get errors, terminate gst first, then dvsource

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
