import requests
import re
from urllib.parse import unquote
from urllib.parse import urlparse
import sys
import time
import os
import json
import m3u8
import subprocess

downloader = "yt-dlp"

def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

def dlvid(url, name, pf, si):
    for path in execute([downloader, "-o", name, url]):
        k = path.replace("~", "").replace("   ", "  ").replace("  ", " ").split(" ")
        if(k[0]=="[download]" and "%" in k[1]):
            prog = float(k[1].replace("%", ""))
            print("\033[1A" + name + " | " + "[" + "="*round((prog/100)*si) + ">" + " "*(si-round((prog/100)*si)) + "] " + ("   " + str(round(prog)))[-3:] + "% | " + k[3] + " | " + pf)
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
    s = re.search("""constsources={'hls':.*};""", r.text.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")).group().split(";")[0].replace("constsources=", "").replace(",}", "}").replace("'", '"')
  #  print(s)
    j = json.loads(s)
#    ur = m3u8.load(j["hls"]).playlists[0].uri
#    return("https://"+urlparse(j["hls"]).netloc+"/"+ur)
    return(j["hls"])

def getvidoza(url):
    r = requests.get(url)
    c = re.search("""<sourcesrc=".*"type='video/mp4'>""", r.text.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")).group().replace('<sourcesrc="', "").replace(""""type='video/mp4'>""", "")
    return(c)

def getvupload(url):
    r = requests.get(url).text
    t = re.search('sources:\[\{src\: \".*', r.replace("\r", "").replace("\n", "").replace("\t", "")).group().split(", type:")[0].replace('sources:[{src: "', "")[0:-1]
    ur = m3u8.load(t).playlists[1].uri
    return(ur)
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
    elif("vupload.com" in url):
        return(("OK", getvupload(url), "vupload.com", "m3u8"))
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
                dlvid(stream[1], output, stream[2], 50)
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

if __name__=="__main__":
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
