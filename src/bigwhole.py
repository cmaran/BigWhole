# -*- encoding: utf-8 -*-

import hashlib
from datetime import datetime, timezone
from functools import wraps
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from flask import Flask
from flask import render_template
from flask import request
from flask import session, redirect, url_for, abort, Response, json
from mailer import Mailer

app = Flask(__name__)
app.secret_key = b'secret' # change for production

client = MongoClient('10.0.104.41', 27017) # change to address of your MongoDB instance
db = client.bigwhole

mailer = Mailer(addr="mail.tgm.ac.at", default_sender="bigwhole@example.org", dummy=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Loggin check")
        if "email" in session:
            user = db.users.find_one({"email" : session["email"]})
            if user != None:
                return f(*args, **kwargs)
        return render_template("no_permission.html")
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "email" in session:
            abort(400)
        user = db.users.find_one({"email" : request.form["email"]})
        if user != None and "password" in user and user["password"] == hashlib.sha256(request.form["password"].encode()).hexdigest():
            session["email"] = user["email"]
            session["uid"] = str(user["_id"])
            return redirect(url_for("index"))
        else:
            return render_template("login.html", failed=True)
    else:
        if "email" in session:
            return redirect(url_for("index"))
        else:
            return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if "email" in session:
            abort(400)
        
        if request.form["email"] == "" or request.form["password"] == "":
            return render_template("register.html", failed=True)

        user = db.users.find_one({"email" : request.form["email"]})
        if user != None and "password" in user:
            return render_template("register.html", exists=True)
        
        if user == None:
            user = {"email" : request.form["email"],
                    "password" : hashlib.sha256(request.form["password"].encode()).hexdigest()}
            db.users.insert(user)
        else:
            print(str(user["_id"]))
            user["password"] = hashlib.sha256(request.form["password"].encode()).hexdigest()
            db.users.save(user)
        return redirect(url_for("login"))
    else:
        if "email" in session:
            return redirect(url_for("index"))
        else:
            return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))

@app.route("/u/list")
def listUsers():
    users = []
    for x in db.users.find():
        users.append(x["email"])
    return render_template("users_list.html", users=users)

@app.route("/e/create", methods=["POST", "GET"])
@login_required
def createEvent():
    if request.method == "POST":
        users = json.loads(request.form["users"])
        event = {"eventtype" : request.form["eventtype"],
                 "name" : request.form["name"],
                 "duration" : request.form["duration"],
                 "users" : [],
                 "owner" : session["email"],
                 "comments" : [],
                 "finished" : False}

        for x in users:
            u = db.users.find_one({"email" : x})
            if u != None:
                event["users"].append(u["_id"])
            else:
                uId = db.users.insert({"email" : x})
                event["users"].append(uId)

        datesRaw = json.loads(request.form["dates"])
        dates = []
        for x in datesRaw:
            dates.append({"date" : datetime.fromtimestamp(x), "users" : []})
        event["dates"] = dates

        eId = db.events.insert(event)

        for x in users:
            mailer.send_mail(x, "You've been invited to an event", "You have been invitet to: " + event["name"] + "\nURL: " + url_for("viewEvent", eId=str(eId), _external=True))

        return "OK"
    else:

        return render_template("event_create.html", registeredUsers=db.users.distinct("email"))

@app.route("/e/view/<eId>")
def viewEvent(eId):
    try:
        event = db.events.find_one({"_id" : ObjectId(eId)})
    except InvalidId:
        abort(404)
    if event != None:
        # convert date to local timezone and fromat as nice string
        dates = []
        for x in event["dates"]:
            dates.append(x["date"].strftime("%H:%M, %d.%m.%Y"))

        u = []
        for x in event["users"]:
            user = db.users.find_one({"_id" : x})
            u.append(user["email"])
        event["users"] = u
        event["id"] = str(event["_id"])

        if "finalDate" in event:
            event["finalDate"] = event["finalDate"].strftime("%H:%M, %d.%m.%Y")

        return render_template("event_view.html", event=event, dates=dates)
    else:
        abort(404)

@app.route("/e/accept", methods=["POST"])
def acceptEventDate():
    try:
        event = db.events.find_one({"_id" : ObjectId(request.form["event"])})
    except InvalidId:
        abort(404)

    user = db.users.find_one({"email" : request.form["user"]})
    if user == None:
        abort(400)

    date = datetime.strptime(request.form["date"], "%H:%M, %d.%m.%Y")
    dateMatched = False
    for x in event["dates"]:
        if x["date"] == date:
            x["users"].append(user["_id"])
            dateMatched = True

    if not dateMatched:
        abort(400)

    db.events.save(event)

    return "OK"

@app.route("/e/setfinaldate", methods=["POST"])
def setFinalEventDate():
    try:
        event = db.events.find_one({"_id" : ObjectId(request.form["event"])})
    except InvalidId:
        abort(404)

    if event["owner"] != session["email"]:
        abort(400)

    date = datetime.strptime(request.form["date"], "%H:%M, %d.%m.%Y")
    dateMatched = False
    for x in event["dates"]:
        if x["date"] == date:
            dateMatched = True

    if not dateMatched:
        abort(400)

    event["finalDate"] = date
    event["finished"] = True

    for x in event["users"]:
        mailer.send_mail(x, "Final date for event set", "The owner has set the final date for the event\"" + event["name"] + "\"\nURL: " + url_for("viewEvent", eId=str(event["_id"]), _external=True))
    
    db.events.save(event)

    return "OK"

@app.route("/e/addcomment", methods=["POST"])
def addComment():
    try:
        event = db.events.find_one({"_id" : ObjectId(request.form["event"])})
    except InvalidId:
        abort(404)

    user = db.users.find_one({"email" : request.form["user"]})
    if user == None:
        abort(400)
    
    event["comments"].append({"user" : user["email"], "comment" : request.form["comment"]})
    db.events.save(event)

    return "OK"

@app.route("/e/deletecomment", methods=["POST"])
def deleteComment():
    try:
        event = db.events.find_one({"_id" : ObjectId(request.form["event"])})
    except InvalidId:
        abort(404)

    if session["email"] != event["owner"]:
        abort(400)

    print(request.form["commentId"])

    try:
        event["comments"].pop(int(request.form["commentId"]))
    except IndexError:
        abort(400)
    
    db.events.save(event)
    return "OK"

@app.route("/e/delete", methods=["POST"])
def deleteEvent():
    try:
        db.events.remove({"_id" : ObjectId(request.form["event"])})
    except InvalidId:
        abort(404)

    return "OK"

@app.route("/u/events")
def userEvents():
    return render_template("user_events.html")

@app.route("/u/eventsjson")
@login_required
def userEventsJSON():
    events = []

    ownedEvents = db.events.find({"owner" : session["email"]})
    for x in ownedEvents:
        events.append([str(x["_id"]), "owned", x["name"]])

    try:
        user = ObjectId(session["uid"])
    except InvalidId:
        abort(400)

    invitedEvents = db.events.find({"users" : user})
    for x in invitedEvents:
        events.append([str(x["_id"]), "invited", x["name"]])

    acceptedEvents = db.events.find({"dates" : {"$elemMatch" : {"users" : user}}})
    for x in acceptedEvents:
        events.append([str(x["_id"]), "accepted", x["name"]])

    return Response(json.dumps({"aaData":events}),  mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
