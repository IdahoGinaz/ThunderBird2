#!/usr/bin/env python3
"""Test RTSP server with appsrc and JPEG frame injection."""
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib
import threading
import time

Gst.init(None)

server = GstRtspServer.RTSPServer()
server.set_property('service', '8558')

# Global to store the first appsrc element
first_appsrc = None
lock = threading.Lock()

class MediaFactory(GstRtspServer.RTSPMediaFactory):
    def do_create_element(self, url):
        global first_appsrc
        
        pipeline_str = (
            'appsrc name=mysrc is-live=true do-timestamp=false ! '
            'queue ! '
            'jpegdec ! '
            'videoscale ! video/x-raw,width=1280,height=720 ! '
            'x264enc speed-preset=ultrafast ! '
            'rtph264pay name=pay0 pt=96'
        )
        pipeline = Gst.parse_launch(pipeline_str)
        source = pipeline.get_by_name('mysrc')
        caps = Gst.Caps.from_string('image/jpeg')
        source.set_property('caps', caps)
        
        if not first_appsrc:
            with lock:
                if not first_appsrc:
                    first_appsrc = source
                    print(f'Captured appsrc: {source}')
        
        return pipeline

factory = MediaFactory()
factory.set_shared(True)

mount_points = server.get_mount_points()
mount_points.add_factory('/camera', factory)

server.attach(None)
print('RTSP appsrc server on port 8558 - waiting for frames...')

# Simple frame injection to test
def inject_frames():
    global first_appsrc
    time.sleep(2)  # Wait for RTSP client to connect
    
    if first_appsrc:
        # Simple small JPEG (1x1 pixel) for testing
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\xff\xd9'
        
        buf = Gst.Buffer.new_wrapped(jpeg_data)
        buf.duration = Gst.SECOND // 5
        
        try:
            result = first_appsrc.emit('push-buffer', buf)
            print(f'Pushed frame, result: {result}')
        except Exception as e:
            print(f'Error pushing frame: {e}')

thread = threading.Thread(target=inject_frames, daemon=True)
thread.start()

loop = GLib.MainLoop()
try:
    loop.run()
except KeyboardInterrupt:
    pass
