#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2016 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-android-accessory/blob/master/LICENSE.

"""
Simple Android Accessory client in Python.
"""

import usb.core
import sys
import time
import random

VID_ANDROID_ACCESSORY = 0x18d1
PID_ANDROID_ACCESSORY = 0x2d01


def get_accessory_dev(ldev):
    """Trigger accessory mode and send the dev handler"""
    set_protocol(ldev)
    set_strings(ldev)
    set_accessory_mode(ldev)
    adev = usb.core.find(
        idVendor=VID_ANDROID_ACCESSORY, 
        idProduct=PID_ANDROID_ACCESSORY
    )
    if adev:
        print "Android accessory mode started"
    return adev


def get_android_dev():
    """Look for a potential Android device"""
    ldev = usb.core.find(bDeviceClass=0)
    if ldev:
        # give time for a mount by the OS
        time.sleep(2)
        # request again a device handler
        ldev = usb.core.find(bDeviceClass=0)
        print "Device found"
        print "VID: {:#04x} PID: {:#04x}".format(
            ldev.idVendor,
            ldev.idProduct
        )
    return ldev


def set_protocol(ldev):
    """Set the USB configuration"""
    try:
        ldev.set_configuration()
    except usb.core.USBError as e:
        if  e.errno == 16:
            pass
        else:
            sys.exit(e)
    ret = ldev.ctrl_transfer(0xC0, 51, 0, 0, 2)
    protocol = ret[0]
    print "Protocol version: {}".format(protocol)
    return


def set_strings(ldev):
    """Send series of strings to activate accessory mode"""
    send_string(ldev, 0, 'Arn-O')
    send_string(ldev, 1, 'PyAndroidAccessory')
    send_string(ldev, 2, 'A Python based Android accessory')
    send_string(ldev, 3, '0.1.1-beta')
    send_string(
        ldev,
        4,
        'https://github.com/Arn-O/py-android-accessory/'
    )
    return


def set_accessory_mode(ldev):
    """Trigger the accessory mode"""
    ret = ldev.ctrl_transfer(0x40, 53, 0, 0, '', 0)    
    assert not ret
    time.sleep(1)
    return


def send_string(ldev, str_id, str_val):
    """Send a given string to the Android device"""
    ret = ldev.ctrl_transfer(0x40, 52, 0, str_id, str_val, 0)
    assert ret == len(str_val)
    return 


def sensor_variation(toss):
    """Return sensor variation"""
    return {
        -10: -1,
        10: 1
    }.get(toss, 0)


def sensor_output(lsensor, variation):
    """Keep the sensor value between 0 and 100"""
    output = lsensor + variation
    if output < 0:
        output = 0
    else:
        if output > 100:
            output = 100
    return output


def communication_loop(ldev):
    """Accessory client to device communication loop"""
    sensor = 50
    while True:
        # random sensor variation
        toss = random.randint(-10, 10)
        sensor = sensor_output(sensor, sensor_variation(toss))
        # write to device
        msg = "S{:04}".format(sensor)
        print "<<< {}".format(msg)
        try:
            ret = ldev.write(0x02, msg, 150)
            assert ret == len(msg)
        except usb.core.USBError as e:
            if e.errno == 19:
                break
            if e.errno == 110:
                # the application has been stopped
                break
            print e
        # read from device
        try:
            ret = ldev.read(0x81, 5, 150)
            sret = ''.join([chr(x) for x in ret])
            print ">>> {}".format(sret)
            if sret == "A1111":
                 variation = -3
            else:
                if sret == "A0000":
                    variation = 3 
            sensor = sensor_output(sensor, variation)
        except usb.core.USBError as e:
            if e.errno == 19:
                break
            if e.errno == 110:
                # a timeout is OK, no message has been sent
                pass
            else:
                print e
        time.sleep(0.2)
    return


def main():
    """Where everything starts"""
    print "Looking for an Android device"
    while True:
        ddev = get_android_dev()
        if not ddev:
            continue
        adev = get_accessory_dev(ddev)
        if not adev:
            continue
        print "Will now communicate with device"
        communication_loop(adev)
        break

if __name__ == '__main__':
    main()
