# -*- coding: utf-8 -*-
import os
from platform import system as system_name  # Returns the system/OS name
from os import system as system_call  # Execute a shell command
import logging
from datetime import date
import time
import smtplib  # Send eamil
import urllib
import socket


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """
    # Ping parameters as function of OS
    ping_param = "-n 1" if system_name().lower() == "windows" else "-c 1"

    # Pinging
    return system_call("ping " + ping_param + " " + host) == 0


def is_website_online(url):
    # return urllib.urlopen(url).getcode() == 200
    # bypass “SSL: CERTIFICATE_VERIFY_FAILED” Error
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    # timeout for 5 second
    socket.setdefaulttimeout(5)
    try:
        code = urllib.urlopen(url).getcode()
    except Exception as e:
        code = 404
    return code == 200


def write_log(log_msg):
    """
    Write log to a file
    :param log_msg:
    :return:
    """
    debug = False
    today = date.today()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)
    if not os.path.isdir('logs'):
        os.mkdir('logs')
    if debug:
        print "[DEBUG] %s" % log_msg
    else:
        logging.basicConfig(filename=dir_path + '/logs/vmm_log_' + str(today) + '.log', level=logging.DEBUG)
        logging.info(log_msg)


def send_email(to_address, subject, body):
    """
    Send email to admin report error
    :param to_address:
    :param subject:
    :param body:
    :return:
    """
    fromaddr = 'send_account@gmail.com'
    toaddrs = to_address
    msg = "\r\n".join([
        "From: %s" % fromaddr,
        "To: %s" % toaddrs,
        "Subject: %s" % subject,
        "",
        "%s" % body
    ])
    username = fromaddr
    password = 'password'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()


def main(vm_name, vm_ip, cmd_command):
    # Email receipt report
    admin_email = 'your_email@gmail.com'

    log_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # When pfSense hang due to [zone: pf states] PF states limit reached
    # still can ping from outside, so check by website return code
    if not is_website_online(vm_ip):
        time.sleep(30)
        if not is_website_online(vm_ip):
            write_log("%s :: Connect to VM name [%s], IP/URL [%s] failed" % (log_time, vm_name, vm_ip))
            send_email(admin_email, '[VMM] %s down' % vm_name,
                       'Connect to %s failed, will try to reboot VM\r\nTime: %s' % (vm_ip, log_time))
            # Hard reboot VM
            system_call(cmd_command)
            time.sleep(180)
            log_time = time.strftime("%Y-%m-%d %H:%M:%S")
            if not is_website_online(vm_ip):
                write_log("%s :: Try to reboot VM name [%s], IP/URL [%s] failed" % (log_time, vm_name, vm_ip))
                send_email(admin_email, '[VMM] %s reboot failed' % vm_name,
                           'Try to reboot VM name [%s], IP/URL [%s] failed, please check.\r\nTime: %s'
                           % (vm_name, vm_ip, log_time))
            else:
                write_log("%s :: Reboot VM name [%s], IP/URL [%s] success, host is online" % (log_time, vm_name, vm_ip))
                send_email(admin_email, '[VMM] %s reboot success' % vm_name,
                           'Reboot [%s], IP/URL [%s] success, host is online.\r\nTime: %s' % (vm_name, vm_ip, log_time))
        else:
            write_log("%s :: Connect to VM name [%s], IP/URL [%s] success (retry 2)" % (log_time, vm_name, vm_ip))
    else:
        write_log("%s :: Connect to VM name [%s], IP/URL [%s] success" % (log_time, vm_name, vm_ip))

# name of VMware VM
server_name = 'pfSense-ABC'
# IP to ping or URL check VM
server_ip = 'https://192.168.1.1:4433'
# Command to reboot VM
# In windows, use cmd command: dir /x to find shortname of directory / file
# example: cmd = 'C:\\PROGRA~1\\VMware\\VMWARE~1\\vmrun -t ws reset D:\\FAS\\WINDOW~1.VMX'
cmd = 'C:\\PROGRA~1\\VMware\\VMWARE~1\\vmrun -t ws reset D:\\pfSense\\FreeBSD.vmx'

main(server_name, server_ip, cmd)
