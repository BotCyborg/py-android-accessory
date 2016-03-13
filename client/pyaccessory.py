#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2016 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-android-accessory/blob/dev/LICENSE.

"""
Simple Android Accessory client in Python.
"""

import usb.core
import sys
import time
import random

VID_ANDROID_ACCESSORY = 0x18d1
PID_ANDROID_ACCESSORY = 0x2d01

def get_accessory():
    print('Looking for Android Accessory')
    print('VID: 0x%0.4x - PID: 0x%0.4x'
        % (VID_ANDROID_ACCESSORY, PID_ANDROID_ACCESSORY))
    dev = usb.core.find(idVendor=VID_ANDROID_ACCESSORY, 
                        idProduct=PID_ANDROID_ACCESSORY)
    return dev

def get_android_device():
    """Look for a potential Android device"""
    print "Looking for an Android device"
    ldev = usb.core.find(bDeviceClass=0)
    if ldev:
        print "Device found"
        print "VID: {:#04x} PID: {:#04x}".format(
            ldev.idVendor,
            ldev.idProduct
        )
    else:
        sys.exit("No Android device found")
    return ldev

def set_protocol(ldev):
    """Set the USB configuration"""
    #try:
    ldev.set_configuration()
    #except usb.core.USBError as e:
    #if  e.errno == 16:
    #        print('Device already configured, should be OK')
    #    else:
    #        sys.exit('Configuration failed')
    ret = ldev.ctrl_transfer(0xC0, 51, 0, 0, 2)
    print ret
    protocol = ret[0]
    print('Protocol version: %i' % protocol)
    if protocol < 2:
        sys.exit('Android Open Accessory protocol v2 not supported')
    return

def set_strings(ldev):
    """Send series of strings to activate accessory mode"""
    send_string(ldev, 0, 'Arn-O')
    send_string(ldev, 1, 'PyAndroidAccessory')
    send_string(ldev, 2, 'A Python based Android accessory')
    send_string(ldev, 3, '0.1.0-beta')
    send_string(ldev, 4, 
            'https://github.com/Arn-O/py-android-accessory/')
    return

def set_accessory_mode(ldev):
    """Trigger the accessory mode"""
    ret = ldev.ctrl_transfer(0x40, 53, 0, 0, '', 0)    
    assert not ret
    time.sleep(1)
    return

def send_string(ldev, str_id, str_val):
    """Send a give string to the Android device"""
    ret = ldev.ctrl_transfer(0x40, 52, 0, str_id, str_val, 0)
    assert ret == len(str_val)
    return 

def start_accessory_mode():
    """Start the accessory mode on the Android device"""
    #dev = get_accessory()
    #if not dev:
    #print('Android accessory not found')
    #print('Try to start accessory mode')
    dev = get_android_device()
    #set_protocol(dev)
    set_strings(dev)
    set_accessory_mode(dev)
    dev = get_accessory()
    #if not dev:
        #sys.exit('Unable to start accessory mode')
    #print('Accessory mode started')
    return dev

def sensor_variation(toss):
    return {
        -10: -1,
        10: 1
    }.get(toss, 0)

def sensor_output(lsensor, variation):
    output = lsensor + variation
    if output < 0:
        output = 0
    else:
        if output > 100:
            output = 100
    return output

def wait_for_command(ldev):
    sensor = 50
    while True:
        try:
            toss = random.randint(-10, 10)
            if sensor + sensor_variation(toss) in range(0, 101):
                sensor = sensor + sensor_variation(toss)
            print ('Sensor: %i' % sensor)
            msg = ('S%0.4i' % sensor)
            print('<<< ' + msg),
            try:
                ret = ldev.write(0x02, msg, 150)
                if ret == len(msg):
                    print(' - Write OK')
            except usb.core.USBError as e:
                print e

            try:
                ret = ldev.read(0x81, 5, 150)
                sret = ''.join([chr(x) for x in ret])
                print('>>> '),
                print sret
                if sret == "A1111":
                    variation = -3
                else:
                    if sret == "A0000":
                        variation = 3 
                sensor = sensor_output(sensor, variation)
            except usb.core.USBError as e:
                if e.errno == 110:
                    pass
                else:
                    print
                    print e
            time.sleep(0.2)
        except KeyboardInterrupt:
            print "Bye!"
            break
        

#        msg='test'

    return

def main():
    """Where everything starts"""
    dev = start_accessory_mode()
    if dev:
        print "Accessory mode started"
    #wait_for_command(dev)

if __name__ == '__main__':
    main()
