import requests
import re
from urllib.parse import unquote
import sys
import time
import os
import json
import m3u8
def dlvid(url, name, pl, si):
    chunk_size = 1024*20
    count = 0
    startb = 0
    try:
        fr = open(name+".part", "rb")
        fw = open(name, "wb")
        while(True):
            t = fw.write(fr.read(chunk_size))
            count += t
            if(t==0):
                startb = count
                break
    except:
        fw = open(name, "wb")
    try:
        r = requests.get(url, stream=True, timeout=10, headers={"Range":"bytes="+str(startb)+"-"})
        size = int(r.headers['Content-length'])+startb
        for chunk in r.iter_content(chunk_size=chunk_size):
            count += fw.write(chunk)
            print("\033[1A" + name + " | " + "[" + "="*round(count/((int(size))/(si))) + ">" + " "*(si-round(count/((int(size))/(si)))) + "] " + ("   " + str(round(count/((int(size))/(100)))))[-3:] + "% | " + (" "*5 + str(round(((count/1024)/1024)*1000)/1000).split(".")[0] + "," + (str(round(((count/1024)/1024)*1000)/1000).split(".")[1] + "000")[0:3] + "/" + str(round(((size/1024)/1024)*1000)/1000).split(".")[0] + "," + (str(round(((size/1024)/1024)*1000)/1000).split(".")[1] + "000")[0:3])[-15:] + " MB | " + pl)
        fw.close()
        try:
            os.remove(name+".part")
        except:
            pass
    except:
        os.rename(name, name+".part")
        1/0

def dlm3u8(url, name, pf, si):
    m3upl = requests.get(url).text.split("\n")
    pl = ""
    for a in m3upl:
        if("https://"in a):
            pl = a
            break
    seg = requests.get(pl).text
    segl = m3u8.loads(seg)
    pl = []
    urla = "/".join(url.split("/")[0:-1])
    for a in segl.segments:
        pl.append(urla+"/"+a.uri)

    fw = open(name+".ts", "wb")

    pcoun = 0
    pllen = len(pl)
    for a in pl:
        chunk_size = 1024*20
        count = 0
        startb = 0
        pcoun += 1
        r = requests.get(a, stream=True, timeout=10, headers={"Range":"bytes="+str(startb)+"-"})
        size = int(r.headers['Content-length'])+startb
        for chunk in r.iter_content(chunk_size=chunk_size):
            count += fw.write(chunk)
            print("\033[1A" + name + " | " + "[" + "="*round(count/((int(size))/(si))) + ">" + " "*(si-round(count/((int(size))/(si)))) + "] " + " | " + ("   " + str(round(pcoun/((pllen)/(100)))))[-3:] + "% | " + str(pcoun)+"/"+str(pllen)+ " | " + pf)
#=PLATFORMS=====================================================================
def getvivo(url):
    html = requests.get(url).text
    t = re.search("(?s)InitializeStream\s*\(\s*(\{.+?})\s*\)\s*;", html).group().split("\n")
    k = ""
    for a in t:
        if("source" in a):
            k = a.replace("	", "").replace("source: '", "").replace("',", "")
    r = unquote(k)
    x = []
    for i in range(len(r)):
        j = ord(r[i])
        if j >= 33 and j <= 126:
            x.append(chr(33 + ((j + 14) % 94)))
        else:
            x.append(r[i])
    return ''.join(x)

def getsendfox(url):
    html = requests.get(url).text
    t = re.search("<textarea.*</textarea>", html).group()
    t = re.search(">.*<", t).group().replace("<", "").replace(">", "")
    return(t)

def getvoe(url):
    r = requests.get(url)
    s = re.search("""constsources={"hls":.*};""", r.text.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")).group().split(";")[0].replace("constsources=", "").replace(",}", "}")
    j = json.loads(s)
    return(j["hls"])

def getvidoza(url):
    r = requests.get(url)
    c = re.search("""<sourcesrc=".*"type='video/mp4'>""", r.text.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")).group().replace('<sourcesrc="', "").replace(""""type='video/mp4'>""", "")
    return(c)

def getvupload(url):
    r = requests.get(url).text
    t = re.search('sources:\[\{src\: \".*', r.replace("\r", "").replace("\n", "").replace("\t", "")).group().split(", type:")[0].replace('sources:[{src: "', "")[0:-1]
    return(t)
#===============================================================================
def getvideo(url):
    if("vivo.sx" in url or "vivo.st" in url):
        return(("OK", getvivo(url), "vivo.sx", "mp4"))
    #elif("sendfox.org" in url):
    #    return(("OK", getsendfox(url), "sendfox.org"))
    elif("voe.sx" in url):
        return(("OK", getvoe(url), "voe.sx", "m3u8"))
    elif("vidoza.net" in url):
        return(("OK", getvidoza(url), "vidoza.net", "mp4"))
#    elif("vupload.com" in url):
#        return(("OK", getvupload(url), "vupload.com", "m3u8"))
    else:
        return(("ERR", "", ""))

def downloadvideo(url, output):
    while(True):
        try:
            print("\033[2KStart Downloading " + url)
            stream = getvideo(url)
            if(stream[0]!="OK"):
                print("\033[1A\033[2KError Dowloading " + url)
                break
            if(stream[3]=="mp4"):
                dlvid(stream[1], output, stream[2], 50)
            elif(stream[3]=="m3u8"):
                dlm3u8(stream[1], output, stream[2], 50)
            break
        except KeyboardInterrupt:
            print("\033[2KKeyboardInterrupt")
            break
        except:
            print("\033[1A\033[2KError Downloading, retry\033[1A")
            time.sleep(1)

def dlfile(file, folder):
    try:
        dllist = open(file).read().split("\n")
        for a in dllist:
            if(not a=="" and not a[0]=="#"):
                downloadvideo(a.split(", ")[1], (folder+"/"+a.split(", ")[0]).replace("//", "/"))
    except KeyboardInterrupt:
        print("\033[2KKeyboardInterrupt")

i = sys.argv[1:]
mf = False
file = False
if("--help" in i or "-h" in i):
    print("Download a single file with [<url> <output-file>]\nDownload from a Download-List with [-f dllist.txt ./video-folder]")
    exit()
for a in i:
    if(a=="-f"):
        mf = True
    elif(mf):
        file = a
        mf = False
if(not file==False):
    dlfile(file, i[-1])
else:
    downloadvideo(i[-2], i[-1])
