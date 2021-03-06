from flask import Flask, render_template, request, redirect
from pathlib import Path
from random import choice
from time import time
import os

#--------------------#
def_url = "https://www.youtube.com/watch?v=jeg_TJvkSjg" #The URL address used, when the user doesnt set one
def_time = 15 #The amount of minutes used, when the user does not specify
def_length = 4 #The default length of the shortned link, will incrase itself if the links start running out
deleteExpiredOnStart = True #Wheter or not should the server go through all links and delete expired ones on startup, this could take a while with a lot of links
maxExpiryTime = 75 #The maximum amount of time in days the user can set the expiry time to
lengthLimit = 2048 #A character length limit for the original URL
allowNewLinks = True #Wheter or not it should be possible to generate a new short link, might be useful to set to False, if you plan to shut down the site soon
port = 5000 #The port to host the website on
emergencyShutdownCheck = False #If enabled, a check for a file named ".emergency_shutdown" is made everytime a link is generated or when "/" is loaded, if it exists, the website will appear as if "allowNewLinks" was set to False.
#--------------------#

app = Flask(__name__)

abc = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z"
abc = abc + "," + abc.upper()
abc = abc.split(",")

if not os.path.isdir("links") :
    os.mkdir("links")

def toSeconds(value, type) :
    value = int(value)

    if type == "seconds" :
        return value * 1
    elif type == "minutes" :
        return value * 60
    elif type == "hours" :
        return value * 3600
    elif type == "days" :
        return value * 86400
    elif type == "months" :
        return value * 2592000
    else :
        return toSeconds(value, "minutes")

def genLink(org_url, expire, length) :
    if emergencyShutdownCheck and os.path.isfile(".emergency_shutdown") :
        return "generation disabled"

    if not allowNewLinks :
        return "generation disabled"
    
    short_url = ""

    for i in range(length) :
        short_url = short_url + choice(abc)

    if not (org_url.startswith("https://") or org_url.startswith("http://")) :
        org_url = "http://" + org_url

    if os.path.isdir(Path("links/" + short_url)) :
        print("Oh no! An existing short url was generated. We may be getting spammed.")
        return genLink(org_url, expire, length + 1)

    os.mkdir(Path("links/" + short_url))
    
    with open(Path("links/" + short_url + "/link.txt"), "w") as f :
        f.write(str(org_url))
    
    with open(Path("links/" + short_url + "/expiresOn.txt"), "w") as f :
        f.write(str(round(time()) + expire))
    
    with open(Path("links/" + short_url + "/createdOn.txt"), "w") as f :
        f.write(str(round(time())))
    
    return short_url

def getLink(short_url) :
    short_url = short_url.replace(".","")

    if not os.path.isdir(Path("links/" + short_url)) :
        return "none"
    
    with open(Path("links/" + short_url + "/expiresOn.txt"), "r") as f :
        expiresOn = int(f.read())
    
    if time() > expiresOn :
        try :
            os.remove(Path("links/" + short_url + "/link.txt"))
        except :
            pass
        return "none"
    
    with open(Path("links/" + short_url + "/link.txt"), "r") as f :
        return str(f.read())

if deleteExpiredOnStart :
    for x in os.listdir("links") :
        try :
            getLink(x)
        except :
            pass

#---------------

@app.route("/", methods=['GET'])
def home():
    if emergencyShutdownCheck and os.path.isfile(".emergency_shutdown") :
        return render_template("generation_disabled.html")

    if allowNewLinks :
        return render_template("main.html", def_url=def_url, def_time=def_time, max_length=lengthLimit)
    else :
        return render_template("generation_disabled.html")

@app.route("/api/new_link", methods=['POST'])
def apiNewLink() :
    org_url = request.form["org_url"]
    expire_value_org = request.form["expire_value"].split(".")[0]
    expire_type = request.form["expire_type"]

    expire_value = ""

    for x in str(expire_value_org) :
        try :
            if int(x) in range(10) :
                expire_value = expire_value + str(x)
        except :
            pass

    if org_url.strip() == "" or org_url == "none" or len(org_url) > lengthLimit :
        org_url = def_url
    
    if expire_value.strip() == "" :
        expire_value = def_time

    expire_seconds = toSeconds(expire_value, expire_type)

    if expire_seconds > maxExpiryTime * 86400 : 
        return render_template("overTimeLimit.html", limit=str(maxExpiryTime))

    short_link = genLink(org_url, expire_seconds, def_length)

    if request.headers.get('User-Agent') == "api" :
        return(short_link)
    else :
        if short_link == "generation disabled" :
            return redirect("../")
        return render_template("success.html", link=request.base_url.strip("api/new_link") + "/" + short_link)

@app.route("/api/get_link/<link>", methods=['GET'])
def apiGetLink(link) :
    short_url = getLink(link)
    return short_url

@app.route("/<link>", methods=['GET'])
def link(link) :
    org_url = getLink(link)
    if org_url == "none" :
        return render_template("invalid_link.html")
    else :
        try :
            return redirect(org_url)
        except :
            return redirect(def_url)

if __name__ == "__main__" :
    app.run(threaded=True, host="0.0.0.0", port=port)