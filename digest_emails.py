import getpass
import os
import sys
import time
from sys import version_info
from optparse import OptionParser
from socket import gaierror
import backports.ssl as ssl

from imapclient import IMAPClient, imapclient

from digesters.digestion_processor import DigestionProcessor


def get_command():
    retval = None

    if check_for_command('git-pull'):
        with open("imapdigester_commands_next_time.sh", 'w+') as f:
            f.write("\ngit pull\nfind . -name \"*.pyc\" -exec rm -rf {} \;\n")
        retval = "BASH-OPERATIONS"

    elif check_for_command('pause'):
        with open("pause_if_present.txt", 'w') as f:
            f.write("")
        retval = "PAUSE"

    elif check_for_command('resume'):
        os.remove('pause_if_present.txt')

    elif os.path.isfile("pause_if_present.txt"):
        retval = "PAUSE"

    return retval


def check_for_command(cmd):
    messages = digest_folder.search('SUBJECT "%s"' % cmd)
    response = digest_folder.fetch(messages, ['FLAGS', 'RFC822.SIZE'])
    retval = False
    for msgid, data in response.iteritems():
        digest_folder.delete_messages([msgid])
        retval = True
    return retval

if __name__ == '__main__':

    reload(sys)
    sys.setdefaultencoding('utf8')

    # Command Line Args

    parser = OptionParser()
    parser.add_option("--notifications-imap", dest="notifications_imap",
                      help="IMAP to use for incoming notifications mail server (SSL assumed)")
    parser.add_option("--notifications-user", dest="notifications_user",
                      help="User ID for incoming notifications mail server")
    parser.add_option("--notifications-pw", dest="notifications_pw",
                      help="User's password for incoming notifications mail server")
    parser.add_option("--notifications-folder", dest="notifications_folder_name", default="INBOX",
                      help="The Imap folder to pull notification from, e.g. INBOX")
    parser.add_option("--notifications-cert-check-skip", action="store_true", dest="notifications_cert_check_skip",
                      help="Skip Certificate check notification imap server (say self-signed)")
    parser.add_option("--digest-imap", dest="digest_imap",
                      help="IMAP to use for outgoing digest (rewrite) mail server (SSL assumed)")
    parser.add_option("--digest-user", dest="digest_user", help="User ID for outgoing digest (rewrite) mail server")
    parser.add_option("--digest-pw", dest="digest_pw",
                      help="User's password for outgoing digest (rewrite) mail server")
    parser.add_option("--digest-folder", dest="digest_folder_name", default="INBOX",
                      help="The Imap folder to pull/push digest from/to, e.g. INBOX")
    parser.add_option("--digest-cert-check-skip", action="store_true", dest="digest_cert_check_skip",
                      help="Skip Certificate check digest imap server (say self-signed)")
    parser.add_option("--implicate", dest="sender_to_implicate",
                      help="Who to name in digest emails, e.g. imapdigester@example.com")
    parser.add_option("--move-unmatched", action="store_true", dest="move_unmatched",
                      help="Move unmatched emails to digest inbox")
    parser.add_option("--print-summary", action="store_true", dest="print_summary", help="Print Summary")

    (options, args) = parser.parse_args()

    old_python = True
    if version_info[0] >= 3:
        old_python = False
    elif version_info[0] == 2 and version_info[1] > 7:
        old_python = False
    elif version_info[0] == 2 and version_info[1] == 7 and version_info[2] >= 11:
        old_python = False
    if old_python and (options.digest_cert_check_skip or options.notifications_cert_check_skip):
        print "Can't do certificate check skipping on Python's less than 2.7.11 (command line options " \
              "--digest-cert-check-skip or --notifications-cert-check-skip)"
        exit(10)

    if options.notifications_pw is None:
        print "Enter notifications user password:"
        options.notifications_pw = getpass.getpass()

    if options.digest_pw is None:
        if options.notifications_imap == options.digest_imap and options.notifications_user == options.digest_user:
            options.digest_pw = options.notifications_pw
        else:
            print "Enter digest user password:"
            options.digest_pw = getpass.getpass()

    notifications_context = None
    if options.notifications_cert_check_skip:
        notifications_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        notifications_context.check_hostname = False
        notifications_context.verify_mode = ssl.CERT_NONE

    # Read and mark for deletion items from notification inbox.
    notification_folder = None
    try:
        if old_python:
            notification_folder = IMAPClient(options.notifications_imap, use_uid=True, ssl=True)
        else:
            notification_folder = IMAPClient(options.notifications_imap, use_uid=True, ssl=True,
                                             ssl_context=notifications_context)
    except gaierror:
        print "CAN'T FIND IMAP SERVER"
        exit(10)
    try:
        notification_folder.login(options.notifications_user, options.notifications_pw)
    except:
        time.sleep(5)
        notification_folder = IMAPClient(options.notifications_imap, use_uid=True, ssl=True,
                                         ssl_context=notifications_context)
        try:
            notification_folder.login(options.notifications_user, options.notifications_pw)
        except:
            print "CAN'T LOG IN to IN IMAP SERVER"
            exit(10)
    time.sleep(1)
    notification_folder.select_folder(options.notifications_folder_name)

    digest_context = None
    if options.digest_cert_check_skip:
        digest_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        digest_context.check_hostname = False
        digest_context.verify_mode = ssl.CERT_NONE

    if old_python:
        digest_folder = IMAPClient(options.digest_imap, use_uid=True, ssl=True)
    else:
        digest_folder = IMAPClient(options.digest_imap, use_uid=True, ssl=True, ssl_context=digest_context)

    try:
        digest_folder.login(options.digest_user, options.digest_pw)
    except:
        time.sleep(5)
        digest_folder.login(options.digest_user, options.digest_pw)
    digest_folder.select_folder(options.digest_folder_name)

    command = get_command()

    if command is None:
        digesters = []

        if os.path.isfile("my_digesters_setup.py"):
            from my_digesters_setup import add_digesters
        else:
            # Copy my_digesters_setup_template.py to the my_digesters_setup.py,
            # if you're wanting to customize the digesters.
            from my_digesters_setup_sample import add_digesters

        # Get Digesters from my_digesters_setup.py
        add_digesters(digesters)

        DigestionProcessor(notification_folder, digest_folder, digesters, options.print_summary,
                           options.sender_to_implicate, options.move_unmatched, options.digest_folder_name)\
            .doit()

    digest_folder.expunge()
    digest_folder.logout()

    notification_folder.expunge()
    notification_folder.logout()

    if command is "BASH-OPERATIONS":
        sys.exit(202)  ## HTTP 'accepted' (FYI)
