#! /usr/bin/python3
#
# @(!--#) @(#) rpass.py, version 003, 07-march-2020
#
# verify and (optionally) change password on one or more Raritan PDUs
#

############################################################################

DEBUG = False

############################################################################

import sys
import os
import argparse
import getpass
import time
import datetime

import raritan.rpc
import raritan.rpc.pdumodel
import raritan.rpc.usermgmt

############################################################################

ADMIN_USERNAME = 'admin'

DEFAULT_HOSTFILE = 'hosts.txt'

############################################################################

def basichostfilevalidation(hostfilename):
    global progname
    
    try:
        hostfile = open(hostfilename, 'r', encoding='utf-8')
    except IOError:
        print('{}: cannot open host file "{}" for reading'.format(progname, hostfilename), file=sys.stderr)
        return -1
    
    hosts     = {}
    hostcount = 0
    linenum   = 0
    
    for line in hostfile:
        linenum += 1
        
        if len(line) == 0:
            continue
            
        if line[0] == '#':
            continue
            
        for host in line.split():
            if host.lower() in hosts:
                print('{}: line {} in host file "{}" has a duplicate entry for host "{}" - see previous line {}'.format(progname, linenum, hostfilename, host, hosts[host.lower()]), file=sys.stderr)
                hostfile.close()
                return -1
            
            hosts[host.lower()] = linenum
            hostcount += 1
    
    hostfile.close()
    
    if hostcount == 0:
        print('{}: host file "{}" does not contain any host names'.format(progname, hostfilename), file=sys.stderr)
        return -1
        
    return hostcount
    
############################################################################

def padoutprompts(firstprompt, secondprompt):
    firstprompt  += ' ...'
    secondprompt += ' ...'
  
    delta = len(firstprompt) - len(secondprompt)
    
    if delta < 0:
        firstprompt += '.' * (delta * -1)
    elif delta > 0:
        secondprompt += '.' * delta

    firstprompt  += ':'
    secondprompt += ':'
    
    return firstprompt, secondprompt
    
############################################################################

def getpassword(prompt1, prompt2):
    prompt1, prompt2 = padoutprompts(prompt1, prompt2)
        
    attempts = 0
    
    while True:
        attempts += 1
        
        if attempts > 3:
            print('Too many attempts - giving up')
            return ''
            
        pw1 = getpass.getpass(prompt1)
        
        if pw1 == '':
            print('Password cannot be null - try again')
            continue
        
        pw2 = getpass.getpass(prompt2)
        
        if pw2 == '':
            print('Password cannot be null - try again')
            continue
        
        if pw1 != pw2:
            print('Passwords do not match - try again')
            continue
        
        return pw1

############################################################################

def detag(html):
    s = ''

    intag = False

    for c in str(html):
        if c == '<':
            intag = True
        elif c == '>':
            intag = False
        elif not intag:
            if c == '\n':
                c = ' '
            s += c

    return s.strip()

############################################################################

def checkhost(host, username, password):
    global progname
    
    agent = raritan.rpc.Agent('https', host, username, password, disable_certificate_verification=True, timeout=5)

    pdu_proxy = raritan.rpc.pdumodel.Pdu('/model/pdu/0', agent)
    
    try:
        nameplate = pdu_proxy.getNameplate()
    except raritan.rpc.HttpException as e:
        print('{}: problem accessing host "{}" - HttpException'.format(progname, host), file=sys.stderr)
        print('{}  {}'.format(' ' * len(progname), detag(e)), file=sys.stderr)
        return ''
        
    return nameplate.serialNumber
            
############################################################################

def checkusernamepassword(hostfilename, username, password):
    global progname
    
    try:
        hostfile = open(hostfilename, 'r', encoding='utf-8')
    except IOError:
        print('{}: cannot open host file "{}" for reading'.format(progname, hostfilename), file=sys.stderr)
        return -1
    
    hosts = {}

    serialnumbers = {}
        
    linenum = 0
    
    hostcount = 0
    
    for line in hostfile:
        linenum += 1
        
        if len(line) == 0:
            continue
            
        if line[0] == '#':
            continue
            
        line = line.strip()
        
        for host in line.split():
            print(host)
            
            if host in hosts:
                print('{}: line {} in host file "{}" has a duplicate entry for host "{}" - see previous line {}'.format(progname, linenum, hostfilename, host, hosts[host]), file=sys.stderr)
                hostfile.close()
                return -1
            
            hosts[host] = linenum
            hostcount += 1
            
            serialnumber = checkhost(host, username, password)
            
            if serialnumber == '':
                print('{}: problem logging into host "{}"'.format(progname, host), file=sys.stderr)
                hostfile.close()
                return -1
                            
            if serialnumber in serialnumbers:
                print('{}: line {} in host file "{}" points to a PDU with the same serial number "{}" - see previous line {}'.format(progname, linenum, hostfilename, serialnumber, serialnumbers[serialnumber]), file=sys.stderr)
                hostfile.close()
                return -1

            serialnumbers[serialnumber] = linenum
    
    hostfile.close()
    
    if hostcount == 0:
        print('{}: host file "{}" does not contain any host names'.format(progname, hostfilename), file=sys.stderr)
        return -1
        
    return hostcount
    
############################################################################

def error2text(error):
    if error == 1:
        text = 'Password Unchanged'
    elif error == 2:
        text = 'Password Empty'
    elif error == 3:
        text = 'Password Too Short'
    elif error == 4:
        text = 'Password Too Long'
    elif error == 5:
        text = 'Password Ctrl Chars'
    elif error == 6:
        text = 'Password Need Lower'
    elif error == 7:
        text = 'Password Need Upper'
    elif error == 8:
        text = 'Password Need Numeric'
    elif error == 9:
        text = 'Password Need Special'
    elif error == 10:
        text = 'Password In History'
    elif error == 11:
        text = 'Password Too Short For SNMP'
    elif error == 12:
        text = 'Invalid Argument'
    elif error == 13:
        text = 'Wrong Password'
    elif error == 14:
        text = 'Ssh Pubkey Data Too Large'
    elif error == 15:
        text = 'Ssh Pubkey Invalid'
    elif error == 16:
        text = 'Ssh Pubkey Not Supported'
    elif error == 17:
        text = 'Ssh RSA Pubkey Too Short'
    else:
        text = 'Unknown error code (rc={})'.format(error)

    return text

############################################################################

def setpass(host, username, password, newpassword):
    agent = raritan.rpc.Agent('https', host, username, password, disable_certificate_verification=True, timeout=5)

    user_proxy = raritan.rpc.usermgmt.User('/auth/user/{}'.format(username), agent)

    userinfo = user_proxy.getInfo()
    
    try:
        rc = user_proxy.setAccountPassword(newpassword)
    except raritan.rpc.HttpException as e:
        print('{}: problem changing password on host "{}" - HttpException'.format(progname, host), file=sys.stderr)
        print('{}  {}'.format(' ' * len(progname), detag(e)), file=sys.stderr)
        return 1
        
    if rc != 0:
        print('{}: password change on host "{}" failed with return code={}'.format(progname, host, rc), file=sys.stderr)
        print('{}  {}'.format(' ' * len(progname), error2text(rc)), file=sys.stderr)
        return 1
    
    return 0

############################################################################

def setnewpasswords(hostfilename, username, password, newpassword):
    global progname
    
    try:
        hostfile = open(hostfilename, 'r', encoding='utf-8')
    except IOError:
        print('{}: cannot open host file "{}" for reading'.format(progname, hostfilename), file=sys.stderr)
        False
        
    for line in hostfile:
        if len(line) == 0:
            continue
            
        if line[0] == '#':
            continue
            
        line = line.strip()
        
        for host in line.split():
            print(host)

            rc = setpass(host, username, password, newpassword)
            
            if rc != 0:
                hostfile.close()
                return False
                
    hostfile.close()
    
    return True
    
############################################################################

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--hostfile',      help='directory to save screenshots to', default=DEFAULT_HOSTFILE)
    parser.add_argument('username',        help='username to login as')
        
    args = parser.parse_args()
    
    hostfilename = args.hostfile
    username = args.username
    
    if username.lower() == ADMIN_USERNAME.lower():
        print('{}: cannot change the admin user "{}" with this utility'.format(progname, username), file=sys.stderr)
        return 1
    
    hostcount = basichostfilevalidation(hostfilename)
    
    if hostcount == -1:
        return 1
    
    if hostcount == 1:
        msg = 'There is 1 host'
    else:
        msg = 'There are {} hosts'.format(hostcount)

    print('{} in host file "{}"'.format(msg, hostfilename))

    password = getpassword('Enter password for user {}'.format(username), 'Enter password again for verification')
    
    if password == '':
        return 1
    
    print('Checking username and password works on all hosts')
    hostcount = checkusernamepassword(hostfilename, username, password)
    
    if hostcount == -1:
        return 1
        
    yesno = input('All hosts ok.  Would you like to proceed and change passwords (y/n)? ')
    
    if (yesno.lower() != 'y') and (yesno.lower() != 'yes'):
        print('OK, maybe later.  Program stopped by user')
        return 0

    newpassword = getpassword('Enter new password for user {}'.format(username), 'Enter password again for verification')
    
    if newpassword == '':
        return 1
        
    if newpassword == password:
        print('New password is the same as the old password - quitting')
        return 1
        
    if setnewpasswords(hostfilename, username, password, newpassword) == False:
        return 1
    
    return 0

############################################################################

progname = os.path.basename(sys.argv[0])

try:
    sys.exit(main())
except KeyboardInterrupt:
    print('')
    print('*** Program stopped by user typing Ctrl^C or Ctrl^Break ***')
    sys.exit(1)
     
# end of file
