#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# util.py

from pathlib import Path
import os
import datetime
import dateutil.parser
import logging

from PyQt5.QtCore import QStandardPaths, QCoreApplication, QDir, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication

from artisanlib.util import d as decode

from roasterhub import config

# we set the app name temporary to "Artisan" to have ArtisanViewer using the same data location as Artisan
app = QCoreApplication.instance()
appName = app.applicationName()
app.setApplicationName("Roasterhub ext")
data_dir = QStandardPaths.standardLocations(QStandardPaths.AppLocalDataLocation)[0]
app.setApplicationName(appName)

# Files


# we store data in the user- and app-specific local default data directory for the platform
# note that the path is based on the ApplicationName and OrganizationName setting of the app
# eg. /Users/<username>/Library/Application Support/Artisan-Scope/Artisan on macOS
def getDataDirectory():
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir
    except Exception as e:
        config.logger.error("util: Exception in getDataDirectory() %s", e)
        return None


# if share is True, the same (cache) file is shared between the Artisan and ArtisanViewer apps
# and locks have to be used to avoid race conditions
def getDirectory(filename, ext=None, share=False):
    fn = filename
    if not share:
        if app.artisanviewerMode:
            fn = filename + "_viewer"
    fp = Path(getDataDirectory(), fn)
    if ext is not None:
        fp = fp.with_suffix(ext)
    try:
        fp = fp.resolve()  # older pathlib raise an exception if a path does not exist
    except:
        pass
    return str(fp)

# returns the last modification date as EPOCH (float incl. milliseconds) of the given file if it exists, or None
def getModificationDate(path):
#    return Path(path).stat().st_mtime
    try:
        return os.path.getmtime(Path(path))
    except Exception as e:
        config.logger.error("util: Exception in getModificationDate() %s", e)
        return None

# Timestamps


# given a datetime object returns e.g. '2018-10-12T12:55:12.999Z'
def datetime2ISO8601(dt):
    (dtstr, micro) = dt.strftime('%Y-%m-%dT%H:%M:%S.%f').split('.')
    return "%s.%03dZ" % (dtstr, int(micro) / 1000)


def ISO86012datetime(ts):
    dt = dateutil.parser.parse(ts)
    return dt  # dt.replace(tzinfo=None)


def datetime2epoch(dt):
    return dt.timestamp()


def epoch2datetime(epoch):
    return datetime.datetime.utcfromtimestamp(epoch)


# given a epoch returns e.g. '2018-10-12T12:55:12.999Z'
def epoch2ISO8601(epoch):
    return datetime2ISO8601(epoch2datetime(epoch))


def ISO86012epoch(ts):
    return datetime2epoch(ISO86012datetime(ts))


def getGMToffset():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset() // datetime.timedelta(seconds=1)


# Prepare Temperatures for sending

def fromFtoC(Ffloat):
    if Ffloat in [-1, None]:
        return Ffloat
    else:
        return (Ffloat-32.0)*(5.0/9.0)


def temp2C(temp):
    if temp is not None and config.app_window.qmc.mode == "F":  # @UndefinedVariable
        return fromFtoC(temp)  # @UndefinedVariable
    else:
        return temp

# Prepare Floats for sending


# in addition to float2float restricting to n decimals this one returns integers if possible
def float2floatMin(fs, n=1):
    if fs is None:
        return None
    else:
        f = config.app_window.float2float(float(fs), n)  # @UndefinedVariable
        i = int(f)
        if f == i:
            return i
        else:
            return f


# Prepare numbers for sending
# for numbers out of range None is returned
def limitnum(minn, maxn, n):
    if n is None or n > maxn or n < minn:
        return None
    else:
        return n


# Prepare temperature in C to the interval [-50,1000] for sending
# for numbers out of range None is returned
def limittemp(temp):
    if temp is None or temp > 1000 or temp < -50:
        return None
    else:
        return temp


# Prepare time in s to the interval [0,3600] for sending
# for numbers out of range None is returned
def limittime(tx):
    if tx is None or tx > 3600 or tx < 0:
        return None
    else:
        return tx


# Prepare text for sending
# text longer than maxlen gets truncated and an eclipse added
def limittext(maxlen, s):
    if s is not None:
        if len(s) > maxlen:
            return s[:maxlen] + ".."
        else:
            return s 
    else:
        return s


# Dicts

def addString2dict(dict_source, key_source, dict_target, key_target, maxlen):
    if key_source in dict_source and dict_source[key_source]:
        txt = limittext(maxlen, decode(dict_source[key_source]))
        if txt is not None:
            dict_target[key_target] = txt


def addNum2dict(dict_source, key_source, dict_target, key_target, minn, maxn, digits):
    if key_source in dict_source and dict_source[key_source]:
        n = limitnum(minn, maxn, dict_source[key_source])
        if n is not None:
            dict_target[key_target] = float2floatMin(n, digits)


# consumes a list of source-target pairs, or just strings used as both source and target key,
# to be processed with add2dict
def addAllNum2dict(dict_source, dict_target, key_source_target_pairs, minn, maxn, digits):
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addNum2dict(dict_source, key_source, dict_target, key_target, minn, maxn, digits)


def addTime2dict(dict_source, key_source, dict_target, key_target):
    if key_source in dict_source and dict_source[key_source]:
        tx = limittime(dict_source[key_source])
        if tx is not None:
            dict_target[key_target] = float2floatMin(tx)


# consumes a list of source-target pairs, or just strings used as both source and target key,
# to be processed with add2dict
def addAllTime2dict(dict_source, dict_target, key_source_target_pairs):
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addTime2dict(dict_source, key_source, dict_target, key_target)


def addTemp2dict(dict_source, key_source, dict_target, key_target):
    if key_source in dict_source and dict_source[key_source]:
        temp = limittemp(temp2C(dict_source[key_source]))
        if temp is not None:
            dict_target[key_target] = float2floatMin(temp)


# consumes a list of source-target pairs, or just strings used as both source and target key,
# to be processed with add2dict
def addAllTemp2dict(dict_source, dict_target, key_source_target_pairs):
    for p in key_source_target_pairs:
        if isinstance(p, tuple):
            (key_source, key_target) = p
        else:
            key_source = key_target = p
        addTemp2dict(dict_source, key_source, dict_target, key_target)


# returns extends dict_target by item with key_target holding the dict_source[key_source] value
# if key_source in dict_source and not empty
def add2dict(dict_source, key_source, dict_target, key_target):
    if key_source in dict_source and dict_source[key_source]:
        dict_target[key_target] = dict_source[key_source]


def getLanguage():
    if config.app_window is not None and config.app_window.plus_account is not None:
        return config.app_window.plus_language
    else:
        return "en"
        
# Open Web Links


def storeLink(plus_store):
    return config.web_base_url + "/" + getLanguage() + "/stores;id=" + str(plus_store)
    

def coffeeLink(plus_coffee):
    return config.web_base_url + "/" + getLanguage() + "/coffees;id=" + str(plus_coffee)


def blendLink(plus_blend):
    return config.web_base_url + "/" + getLanguage() + "/blends;id=" + str(plus_blend)


def roastLink(plus_roast):
    return config.web_base_url + "/" + getLanguage() + "/roasts;id=" + str(plus_roast)


# Logging

def debugLogON():
    config.logger.info("util:debugLogON()")
    config.logger.setLevel(logging.DEBUG)
    config.handler.setLevel(logging.DEBUG)
    config.app_window.sendmessage(
        QApplication.translate("Plus", "artisan.plus debug logging ON.", None)
    )  # @UndefinedVariable


def debugLogOFF():
    config.logger.info("util:debugLogOFF()")
    config.logger.setLevel(logging.INFO)
    config.handler.setLevel(logging.INFO)
    config.app_window.sendmessage(
        QApplication.translate("Plus", "artisan.plus debug logging OFF.", None)
    )  # @UndefinedVariable


def debugLogToggle():
    if config.logger.isEnabledFor(logging.DEBUG):
        debugLogOFF()
    else:
        debugLogON()


def sendLog():
    config.logger.info("util:sendLog()")
    from email import encoders, generator
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    message = MIMEMultipart()
    if config.app_window.plus_email is not None:
        message['From'] = config.app_window.plus_email
    message["To"] = "{}@{}".format(config.log_file_account, config.log_file_domain)
    message["Subject"] = "artisan.plus client log"
    message["X-Unsent"] = "1"
    # message["X-Uniform-Type-Identifier"] = "com.apple.mail-draft"
    message.attach(
        MIMEText(
            "Please find attached the artisan.plus log file written by Artisan!\n"
            "Please forward this email to {}\n--\n".format(message["To"]), "plain"
        )
    )
    with open(config.log_file_path, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)
    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        "attachment; filename= {}{}".format(config.log_file, ".log"))
    # Add attachment to message and convert message to string
    message.attach(part)    
    # Save message to file tmp file
    tmpfile = QDir(QDir.tempPath()).filePath("plus-log.eml")
    try:
        os.remove(tmpfile)
    except OSError:
        pass
    with open(tmpfile, 'w') as outfile:
        gen = generator.Generator(outfile)
        gen.flatten(message)
    QDesktopServices.openUrl(QUrl.fromLocalFile(tmpfile))
