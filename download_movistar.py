import socket
import time
import random
import urllib.request
import json
import os
import optparse
import sys

from datetime import datetime



def download_movistar(productID, serviceuid, path):

  url="http://www-60.svc.imagenio.telefonica.net:2001/appserver/mvtv.do?action=getRecordingData&extInfoID="+productID+"&channelID="+serviceuid+"&mode=1&adType=1"
  with urllib.request.urlopen(url) as pagina:
    s = pagina.read()
    decoded =json.loads(s.decode('utf-8'))
    downloadurl=decoded['resultData']['url']
    valueend=downloadurl.find(":554")
    urlserver="172.26.81.5"#downloadurl[7:valueend]
    name=decoded['resultData']['name']                                                     
    tiempo=decoded['resultData']['endTime'] - decoded['resultData']['beginTime']
    ts = int(decoded['resultData']['beginTime']/1000)
    fecha=datetime.utcfromtimestamp(ts).strftime('%Y%m%d_%H%M')
    name=fecha+name
    tiempo=tiempo/20000
  repetir_bucle = True
  while repetir_bucle:
    port=random.randint(15025,24000)
    req = "  "
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    sock.sendto(req.encode(),(urlserver, 554))
    sock.settimeout(0.5)

    req = "OPTIONS * RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: MICA-IP-STB\r\n\r\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((urlserver, 554))
    s.sendall(req.encode())
    data = s.recv(900)
    req = "DESCRIBE "+downloadurl+" RTSP/1.0\r\nCSeq: 2\r\nUser-Agent: MICA-IP-STB\r\nAccept: application/sdp\r\n\r\n"
    s.sendall(req.encode())
    data = s.recv(900).decode()
    valuestart=data.find("rtsp://")

    url=data[valuestart:]
    req = "SETUP "+url+" RTSP/1.0\r\nCSeq: 3\r\nUser-Agent: MICA-IP-STB\r\nTransport: MP2T/H2221/UDP;unicast;client_port="+str(port)+"\r\nx-mayNotify:\r\n\r\n"
    s.sendall(req.encode())
    data = s.recv(900).decode()
    valuestart=data.find("Session:")
    valueend=data.find(";timeout")
    sesion=data[valuestart+9:valueend]

    req = "PLAY "+url+" RTSP/1.0\r\nCSeq: 4\r\nSession: "+sesion+"\r\nUser-Agent: MICA-IP-STB\r\nRange: npt=0-end\r\nScale: 1.000\r\nx-playNow: \r\nx-noFlush: \r\n\r\n"
    s.sendall(req.encode())
    data = s.recv(900).decode()
    code=data[9:12]
    if code=="200":
      repetir_bucle = False
      pid = os.fork()
      if pid == 0:
    # We are in the child process.
        csec=5
        while tiempo > 0:
          req = "GET_PARAMETER "+url+" RTSP/1.0\r\nUser-Agent: MICA-IP-STB\r\nSession: "+sesion+"\r\nCSeq: "+str(csec)+"\r\nContent-type: text/parameters\r\nContent-length: 10\r\n\r\nposition\r\n"
          csec=csec+1
          s.sendall(req.encode())
          tiempo=tiempo-1
          time.sleep(20)
        quit()
      else:
        timeout=0
        f = open(path+name.replace("/", "-")+".ts", "w+b")
        while timeout==0:
          try:
            data, addr = sock.recvfrom(4096) # buffer size is 1024 bytes
            f.write(bytearray(data))
          except:
            timeout=1

        f.close()
        sock.close()
        quit()
    sock.close()
