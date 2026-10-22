# MeshRadio

Raspberru pi 5 or 4
Trixie 


eeb4dd67e07a24fa8404a684741cf49cdcc0afb646c8ae77efb6f1a1d55c02cf

1 - Install Gstreamer:
    
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-alsa
    
2- Test audio harware:
input
arecord -l
    
Output 
aplay -l

short audio file
https://soccloud.dy.fi/index.php/s/gQj2REPx6Q9sEzF

Long audio file:
https://soccloud.dy.fi/index.php/s/TSWTHZkarkekGKy

To stream audio file

gst-launch-1.0 filesrc location=dj.mp3 ! decodebin ! audioconvert ! audioresample ! audio/x-raw,rate=48000 ! lamemp3enc target=bitrate bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=192.168.1.27 port=5000

To stream from audio input:

gst-launch-1.0  alsasrc device=plughw:1,0 ! decodebin ! audioconvert ! audioresample ! audio/x-raw,rate=48000 ! lamemp3enc target=bitrate bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=192.168.1.27 port=5000

//MY OWN

RPI
gst-launch-1.0 filesrc location=dj.mp3 ! decodebin ! audioconvert ! audioresample ! audio/x-raw,rate=48000 ! lamemp3enc target=bitrate bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=192.168.1.68  port=5000

VLC
udp://@:5000


