#!/home/pi/venv/feeder/bin/python
from __future__ import with_statement
import sys

sys.path.extend(['/var/www/CatFeeder/logs'])
import sqlite3
from flask import Flask, flash, Markup, redirect, render_template, request, Response, session, url_for, abort
import subprocess
import commonTasks
import os
import configparser
import datetime
# from werkzeug import check_password_hash, generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from stat import S_ISREG, ST_CTIME, ST_MODE
import os, sys, time

app = Flask(__name__)

# Find config file
# dir = os.path.dirname(__file__)  # os.getcwd()
# configFilePath = os.path.abspath(os.path.join(dir, "app.cfg"))
configParser = configparser.RawConfigParser()
configParser.read('/var/www/CatFeeder/app.cfg')

# Read in config variables
SECRETKEY = str(configParser.get('CatFeederConfig', 'Secretkey'))
servoGPIO = str(configParser.get('CatFeederConfig', 'Servo_GPIO_Pin'))
servoOpenTime = str(configParser.get('CatFeederConfig', 'Servo_Open_Time'))
DB = str(configParser.get('CatFeederConfig', 'Database_Location'))
latestXNumberFeedTimesValue = str(configParser.get('CatFeederConfig', 'Number_Feed_Times_To_Display'))
upcomingXNumberFeedTimesValue = str(configParser.get('CatFeederConfig', 'Number_Scheduled_Feed_Times_To_Display'))


#####################################################################################
##########################################HOME PAGE##################################
#####################################################################################
@app.route('/', methods=['GET', 'POST'])
def home_page():
    try:

        latestXNumberFeedTimes = commonTasks.db_get_last_feedtimes(latestXNumberFeedTimesValue)

        upcomingXNumberFeedTimes = commonTasks.db_get_scheduled_feedtimes(upcomingXNumberFeedTimesValue)

        finalFeedTimeList = []
        for x in latestXNumberFeedTimes:
            x = list(x)
            dateobject = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S')
            x[0] = dateobject.strftime("%m-%d-%y %I:%M %p")
            x = tuple(x)
            finalFeedTimeList.append(x)

        finalUpcomingFeedTimeList = []
        for x in upcomingXNumberFeedTimes:
            x = list(x)
            dateobject = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S')
            finalString = dateobject.strftime("%m-%d-%y %I:%M %p")

            # 1900-01-01 default placeholder date for daily reoccuring feeds
            if str(x[2]) == '5':  # Repeated schedule. Strip off Date
                finalString = finalString.replace("01-01-00", "Daily at")

            finalUpcomingFeedTimeList.append(finalString)

    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/feedbuttonclick', methods=['GET', 'POST'])
def feedbuttonclick():
    try:
        dateNowObject = datetime.datetime.now()

        turn = commonTasks.rotate_servo(servoGPIO, servoOpenTime)

        if turn != 'ok':
            flash('Error! No feed activated! Error Message: ' + str(turn), 'error')
            return redirect(url_for('home_page'))

        dbInsert = commonTasks.db_insert_feedtime(dateNowObject, 2)  # FeedType 2=Button Click
        if dbInsert != 'ok':
            flash('Warning. Database did not update: ' + str(dbInsert), 'warning')
            return redirect(url_for('home_page'))

        updatescreen = commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())
        if updatescreen != 'ok':
            flash('Warning. Screen feedtime did not update: ' + str(updatescreen), 'warning')
            return redirect(url_for('home_page'))

        flash('Feed success!')
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/feedbuttonclickSmartHome', methods=['GET', 'POST'])
def feedbuttonclickSmartHome():
    try:
        dateNowObject = datetime.datetime.now()

        turn = commonTasks.rotate_servo(servoGPIO, servoOpenTime)
        if turn != 'ok':
            flash('Error! No feed activated! Error Message: ' + str(turn), 'error')
            return redirect(url_for('home_page'))

        dbInsert = commonTasks.db_insert_feedtime(dateNowObject, 4)  # FeedType 4=Smart Home
        if dbInsert != 'ok':
            flash('Warning. Database did not update: ' + str(dbInsert), 'warning')

        updatescreen = commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())
        if updatescreen != 'ok':
            flash('Warning. Screen feedtime did not update: ' + str(updatescreen), 'warning')

        flash('Feed success!')
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/scheduleDatetime', methods=['GET', 'POST'])
def scheduleDatetime():
    try:
        scheduleDatetime = [request.form['scheduleDatetime']][0]
        scheduleTime = [request.form['scheduleTime']][0]

        dateobj = datetime.datetime.strptime(scheduleDatetime, '%Y-%m-%d')
        timeobj = datetime.datetime.strptime(scheduleTime, '%H:%M').time()

        dateobject = datetime.datetime.combine(dateobj, timeobj)

        dbInsert = commonTasks.db_insert_feedtime(dateobject, 0)  # FeedType 0=One Time Scheduled Feed
        if dbInsert != 'ok':
            flash('Error! The time has not been scheduled! Error Message: ' + str(dbInsert), 'error')
            return redirect(url_for('home_page'))

        flash("Time Scheduled")
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/scheduleRepeatingDatetime', methods=['GET', 'POST'])
def scheduleRepeatingDatetime():
    try:
        scheduleRepeatingTime = [request.form['scheduleRepeatingTime']][0]
        timeobj = datetime.datetime.strptime(scheduleRepeatingTime, '%H:%M').time()

        dbInsert = commonTasks.db_insert_feedtime(timeobj, 5)  # FeedType 5=Repeat Daily Scheduled Feed
        if dbInsert != 'ok':
            flash('Error! The time has not been scheduled! Error Message: ' + str(dbInsert), 'error')
            return redirect(url_for('home_page'))

        flash("Time Scheduled")
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/deleteRow/<history>', methods=['GET', 'POST'])
def deleteRow(history):
    try:
        if "Daily at" in history:
            # Scheduled time switch back
            history = history.replace("Daily at", "01-01-1900")
            dateObj = datetime.datetime.strptime(history, "%m-%d-%Y %I:%M %p")
        else:
            dateObj = datetime.datetime.strptime(history, "%m-%d-%y %I:%M %p")

        deleteRowFromDB = deleteUpcomingFeedingTime(str(dateObj))
        if deleteRowFromDB != 'ok':
            flash('Error! The row has not been deleted! Error Message: ' + str(deleteRowFromDB), 'error')
            return redirect(url_for('home_page'))

        flash("Scheduled time deleted")
        return redirect(url_for('home_page'))

    except Exception as e:
        return render_template('error.html', resultsSET=e)


def deleteUpcomingFeedingTime(dateToDate):
    try:
        con = commonTasks.connect_db()
        cur = con.execute("""delete from feedtimes where feeddate=?""", [str(dateToDate), ])
        con.commit()
        cur.close()
        con.close()
        return 'ok'
    except Exception as e:
        return e



######################################################################################
##########################################ADMIN PAGE##################################
######################################################################################

@app.route('/adminLogin', methods=['GET', 'POST'])
def admin_login_page():
    try:

        if 'userLogin' in session:
            return redirect(url_for('admin_page'))
        else:
            return render_template('login.html')

    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/login', methods=['GET', 'POST'])
def login_verify():
    try:

        if 'userLogin' in session:
            return redirect(url_for('admin_page'))
        else:

            if not request.form['usrname']:
                return render_template('error.html', resultsSET="Enter Username")
            elif not request.form['psw']:
                return render_template('error.html', resultsSET="Enter Password")

            user = [request.form['usrname']]
            username = user[0]

            pw = [request.form['psw']]
            password = pw[0]

            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute('''select pw_hash from user where username=?''', [username, ])
            pw_hash = c.fetchone()
            c.close()
            conn.close()

            # Invalid Username (not in DB)
            if not pw_hash:
                con = sqlite3.connect(DB)
                cur = con.execute('''insert into loginLog (loginName,loginPW,loginDate) values (?,?,?)''',
                                  [username, password, datetime.datetime.now()])
                con.commit()
                cur.close()
                con.close()
                return render_template('error.html', resultsSET="Invalid Credentials")
            else:
                pw_hash = pw_hash[0]

            # User in DB (invalid PW)
            if not check_password_hash(pw_hash, password):
                con = sqlite3.connect(DB)
                cur = con.execute('''insert into loginLog (loginName,loginPW,loginDate) values (?,?,?)''',
                                  [username, password, datetime.datetime.now()])
                con.commit()
                cur.close()
                con.close()
                return render_template('error.html', resultsSET="Invalid Credentials")

            session['userLogin'] = str(username)

            return redirect(url_for('admin_login_page'))

    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('userLogin', None)
    return redirect(url_for('admin_login_page'))


@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    try:
        if 'userLogin' in session:
            buttonServiceFullOutput = ControlService('catFeederButtonService', 'status')
            buttonServiceFinalStatus = CleanServiceStatusOutput(str(buttonServiceFullOutput))

            timeServiceFullOutput = ControlService('catFeederTimeService', 'status')
            timeServiceFinalStatus = CleanServiceStatusOutput(str(timeServiceFullOutput))

            sshServiceFullOutput = ControlService('ssh', 'status')
            sshServiceFinalStatus = CleanServiceStatusOutput(str(sshServiceFullOutput))

            walkInServiceFullOutput = ControlService('catFeederWalkInService', 'status')
            walkInServiceFinalStatus = CleanServiceStatusOutput(str(walkInServiceFullOutput))

            # Bad login log
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("select loginName, loginPW, loginDate from LoginLog;")
            invalidLogins = c.fetchall()
            # Return none of no rows so UI knows what to display
            if len(invalidLogins) <= 0:
                invalidLogins = None
            conn.commit()
            conn.close()

            # Current Admins
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("select user_id, username from user;")
            userLogins = c.fetchall()
            # Return none of no rows so UI knows what to display
            if len(userLogins) <= 0:
                userLogins = None
            conn.commit()
            conn.close()

            return render_template('admin.html'
                                   , buttonServiceFinalStatus=buttonServiceFinalStatus
                                   , timeServiceFinalStatus=timeServiceFinalStatus
                                   , sshServiceFinalStatus=sshServiceFinalStatus
                                   , walkInServiceFinalStatus=walkInServiceFinalStatus
                                  #, webcameraServiceFinalStatus=webcameraServiceFinalStatus
                                   , invalidLogins=invalidLogins
                                   , userLogins=userLogins
                                   )

        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/clearBadLoginList', methods=['GET', 'POST'])
def clearBadLoginList():
    try:
        if 'userLogin' in session:

            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("delete from loginLog")
            conn.commit()
            c.close()
            conn.close()

            flash('List cleared')

            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/startWalkInService', methods=['GET', 'POST'])
def startWalkInService():
    try:
        if 'userLogin' in session:
            walkInServiceFullOutput = ControlService('catFeederWalkInService', 'start')
            flash('WalkIn Service Started!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/stopWalkInService', methods=['GET', 'POST'])
def stopWalkInService():
    try:
        if 'userLogin' in session:
            walkInServiceFullOutput = ControlService('catFeederWalkInService', 'stop')

            flash('WalkIn Service Stopped!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/startButtonService', methods=['GET', 'POST'])
def startButtonService():
    try:
        if 'userLogin' in session:
            myLogTimeServiceFullOutput = ControlService('catFeederButtonService', 'start')

            flash('Button Service Started!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/stopButtonService', methods=['GET', 'POST'])
def stopButtonService():
    try:
        if 'userLogin' in session:
            myLogTimeServiceFullOutput = ControlService('catFeederButtonService', 'stop')

            flash('Button Service Stopped!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/startTimeService', methods=['GET', 'POST'])
def startTimeService():
    try:
        if 'userLogin' in session:
            myLogTimeServiceFullOutput = ControlService('catFeederTimeService', 'start')

            flash('Time Service Started!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/stopTimeService', methods=['GET', 'POST'])
def stopTimeService():
    try:
        if 'userLogin' in session:
            myLogTimeServiceFullOutput = ControlService('catFeederTimeService', 'stop')

            flash('Time Service Stopped!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/startSshService', methods=['GET', 'POST'])
def startSshService():
    try:
        if 'userLogin' in session:
            sshServiceFullOutput = ControlService('ssh', 'start')

            flash('SSH Service Started!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/stopSshService', methods=['GET', 'POST'])
def stopSshService():
    try:
        if 'userLogin' in session:
            sshServiceFullOutput = ControlService('ssh', 'stop')

            flash('SSH Service Stopped!')
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


def ControlService(serviceToCheck, command):
    try:

        process = subprocess.Popen(["sudo", "service", serviceToCheck, command],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        return process.stdout.read()
    except Exception as e:
        return render_template('error.html', resultsSET=e)


def CleanServiceStatusOutput(serviceOutput):
    try:
        if serviceOutput.find('could not be found') > 0:
            return str('Inactive')
        elif serviceOutput.find('no tty present not be found') > 0:
            return str('Inactive')
        elif serviceOutput.find('inactive (dead)') > 0:
            ServiceStartString = serviceOutput.find('(dead) since') + len('(dead)')
            ServiceEndString = serviceOutput.find('ago', ServiceStartString)
            ServiceFinalStatus = serviceOutput[ServiceStartString:ServiceEndString]
            return str('Inactive: ' + str(ServiceFinalStatus))
        elif serviceOutput.find('active (running)') > 0:
            ServiceStartString = serviceOutput.find('(running) since') + len('(running)')
            ServiceEndString = serviceOutput.find('ago', ServiceStartString)
            ServiceFinalStatus = serviceOutput[ServiceStartString:ServiceEndString]
            return str('Active: ' + str(ServiceFinalStatus))
        elif serviceOutput.find('active (exited) since') > 0:
            ServiceStartString = serviceOutput.find('active (exited) since') + len('active (exited)')
            ServiceEndString = serviceOutput.find('ago', ServiceStartString)
            ServiceFinalStatus = serviceOutput[ServiceStartString:ServiceEndString]
            return str('Active: ' + str(ServiceFinalStatus))
        else:
            return str(serviceOutput)

    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/history', methods=['GET', 'POST'])
def history_page():
    try:
        if 'userLogin' in session:

            latestXNumberFeedTimes = commonTasks.db_get_last_feedtimes(500)

            finalFeedTimeList = []
            for x in latestXNumberFeedTimes:
                x = list(x)
                dateobject = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S')
                x[0] = dateobject.strftime("%m-%d-%y %I:%M:%S %p")
                x = tuple(x)
                finalFeedTimeList.append(x)

            return render_template('history.html'
                                   , latestXNumberFeedTimes=finalFeedTimeList
                                   )
        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/deleteUser/<id>', methods=['GET', 'POST'])
def deleteUser(id):
    try:
        if 'userLogin' in session:

            con = commonTasks.connect_db()
            cur = con.execute("""delete from user where username=?""", [str(id), ])
            con.commit()
            cur.close()
            con.close()

            flash('User deleted')

            return redirect(url_for('admin_page'))

        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/User', methods=['GET', 'POST'])
def User():
    try:
        if 'userLogin' in session:

            return render_template('user.html')

        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


@app.route('/addUser', methods=['GET', 'POST'])
def addUser():
    try:
        if 'userLogin' in session:

            if not request.form['usrname']:
                return render_template('error.html', resultsSET="Enter Username")
            elif not request.form['psw']:
                return render_template('error.html', resultsSET="Enter Password")

            user = [request.form['usrname']]
            username = user[0]

            pw = [request.form['psw']]
            password = pw[0]

            # Does exists already
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute('''select username from user where username=?''', [username, ])
            userName = c.fetchone()
            c.close()
            conn.close()

            if userName:
                return render_template('error.html', resultsSET="User Name Already Exists")

            # Add to DB
            con = sqlite3.connect(DB)
            cur = con.execute('''insert into user (username,email,pw_hash) values (?,?,?)''',
                              [username, '', generate_password_hash(password)])
            con.commit()
            cur.close()
            con.close()
            flash('User Created')

            return redirect(url_for('admin_page'))

        else:
            return redirect(url_for('admin_login_page'))
    except Exception as e:
        return render_template('error.html', resultsSET=e)


app.secret_key = SECRETKEY

# main
if __name__ == '__main__':
    app.debug = False  # reload on code changes. show traceback
    app.run(host='0.0.0.0', threaded=True)
