import sys
from unittest import TestCase

from mock import Mock, call
from mockextras import stub

from digesters.digestion_processor import DigestionProcessor
from digesters.linkedin.linkedin_invitation_digester import LinkedinInvitationDigester

MAIL_HDR = """From: "Linkedin" <ph@example.com>
Content-Transfer-Encoding: 8bit
Content-Type: multipart/alternative; boundary="---NOTIFICATION_BOUNDARY-5678"
MIME-Version: 1.0
This is a multi-part message in MIME format.
-----NOTIFICATION_BOUNDARY-5678
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 8bit


"""


class InvitationsStore(object):

    def __init__(self, cls=object):
        self._cls = cls
        self.invitations = None

    def __eq__(self, other):
        self.invitations = other
        return True

    def __ne__(self, other):
        return False

    def __repr__(self):
        return "InvitationsStore(..)"


class TestLinkedinInvitations(TestCase):

    def __init__(self, methodName='runTest'):
        super(TestLinkedinInvitations, self).__init__(methodName)
        reload(sys)
        sys.setdefaultencoding('utf8')

    def test_two_related_invitations_can_be_rolled_up(self):

        expected_payload = """<html><body><span>You have previously read invitations up to: Apr 01 2016 06:13 PM</span>
          <table>
            <tr style="background-color: #acf;">
              <th colspan="2">Invitations</th>
            </tr>
                    <tr style="">
              <td><img style="max-width:100px;height:auto" src="https://media.licdn.com/mpr/mpr/shrinknp_100_100/p/4/000/17b/3db/1dbe948.jpg"/></td>
              <td>
                <strong>Steven Footle</strong><br>
                Hi Paul,<br/>
          I\'d like to join your LinkedIn network.<br/>
          Steven Footle<br/>
          Principal Test Architect and Agile Leader - Certified ScrumMaster<br/>
          <br>
                <a href="https://www.linkedin.com/comm/people/invite-accept?mboxid=I6122153999904439999_500&sharedKey=-aWVMgrZ&fr=false&invitationId=6122153757099996400&fe=true&trk=eml-comm_invm-b-accept-newinvite&midToken=AQHQ1w999ws4wA&trkEmail=eml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%7Ejk">Accept Invitation</a>
                <a href="https://www.linkedin.com/comm/profile/view?id=AAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA&authType=name&authToken=F40O&invAcpt=2197625_I6122153999904439999_500&midToken=AQHQ1w999ws4wA&trk=eml-M2M_Invitation-hero-1-text%7Eprofile&trkEmail=eml-M2M_Invitation-hero-1-text%7Eprofile-null-1b3p5%7Eimjp489e%999k">View Profile</a>
              </td>
            </tr>          <tr><td colspan="2" style="border-bottom: 1pt solid red; border-top: 1pt solid red;"><center>^ New Invitations Since You Last Checked ^</center></td></tr>          <tr style="background-color: #def;">
              <td><img style="max-width:100px;height:auto" src="https://media.licdn.com/mpr/mpr/shrinknp_100_100/p/4/000/17b/3db/1dbe948.jpg"/></td>
              <td>
                <strong>Steven Blipvert</strong><br>
                Hi Paul,<br/>
          I\'d like to join your LinkedIn network.<br/>
          Steven Blipvert<br/>
          Principal Test Architect and Agile Leader - Certified ScrumMaster<br/>
          <br>
                <a href="https://www.linkedin.com/comm/people/invite-accept?mboxid=I6122153999904439999_500&sharedKey=-aWVMgrZ&fr=false&invitationId=6122153757099996400&fe=true&trk=eml-comm_invm-b-accept-newinvite&midToken=AQHQ1w999ws4wA&trkEmail=eml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%7Ejk">Accept Invitation</a>
                <a href="https://www.linkedin.com/comm/profile/view?id=AAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA&authType=name&authToken=F40O&invAcpt=2197625_I6122153999904439999_500&midToken=AQHQ1w999ws4wA&trk=eml-M2M_Invitation-hero-1-text%7Eprofile&trkEmail=eml-M2M_Invitation-hero-1-text%7Eprofile-null-1b3p5%7Eimjp489e%999k">View Profile</a>
              </td>
            </tr>
          </table></body></html>""".replace("\n          ","\n")

        notification_store = {}

        final_invitations_store = InvitationsStore()

        store_writer = Mock()
        store_writer.get_from_binary.side_effect = stub(
            (call('linkedin-invitations'), notification_store),
            (call('most-recently-seen'), 1459548811)
        )
        store_writer.store_as_binary.side_effect = stub(
            (call('linkedin-invitations', final_invitations_store), True),
            (call('most-recently-seen', 1459548811), True)
        )

        expected_message = ("Subject: Invitation Digest: 1 new invitation(s)\n" + MAIL_HDR + expected_payload + \
                           "\n\n-----NOTIFICATION_BOUNDARY-5678")

        digest_inbox_proxy = Mock()
        digest_inbox_proxy.delete_previous_message.side_effect = stub((call(), True))
        digest_inbox_proxy.append.side_effect = stub((call(expected_message), True))

        digesters = []
        digester = LinkedinInvitationDigester(store_writer)  ## What we are testing
        digester.notification_boundary_rand = "-5678"  # no random number for the email's notification boundary
        digesters.append(digester)

        digestion_processor = DigestionProcessor(None, None, digesters, False, "ph@example.com", False, "INBOX")

        unmatched_to_move = []
        to_delete_from_notification_folder = []

        notification_2_content = INCOMING_1.replace("Footle", "Blipvert").replace("4 Apr 2016", "1 Apr 2016")

        digestion_processor.process_incoming_notification(1234, digesters, INCOMING_1, to_delete_from_notification_folder, unmatched_to_move, False)
        digestion_processor.process_incoming_notification(1235, digesters, notification_2_content, to_delete_from_notification_folder, unmatched_to_move, False)

        digester.rewrite_digest_emails(digest_inbox_proxy, has_previous_message=True,
                                       previously_seen=False, sender_to_implicate="ph@example.com")

        self.assertEquals(digest_inbox_proxy.mock_calls, [call.delete_previous_message(), call.append(expected_message)])

        calls = store_writer.mock_calls
        self.assertEquals(calls, [
            call.get_from_binary('linkedin-invitations'),
            call.get_from_binary('most-recently-seen'),
            call.store_as_binary('linkedin-invitations', {
                1459808011: {
                    'spiel': "Hi Paul,\nI'd like to join your LinkedIn network.\nSteven Footle\nPrincipal Test Architect and Agile Leader - Certified ScrumMaster\n",
                    'accept_url': 'https://www.linkedin.com/comm/people/invite-accept?mboxid=I6122153999904439999_500&sharedKey=-aWVMgrZ&fr=false&invitationId=6122153757099996400&fe=true&trk=eml-comm_invm-b-accept-newinvite&midToken=AQHQ1w999ws4wA&trkEmail=eml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%7Ejk',
                    'who': 'Steven Footle',
                    'img_src': 'https://media.licdn.com/mpr/mpr/shrinknp_100_100/p/4/000/17b/3db/1dbe948.jpg',
                    'profile_url': 'https://www.linkedin.com/comm/profile/view?id=AAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA&authType=name&authToken=F40O&invAcpt=2197625_I6122153999904439999_500&midToken=AQHQ1w999ws4wA&trk=eml-M2M_Invitation-hero-1-text%7Eprofile&trkEmail=eml-M2M_Invitation-hero-1-text%7Eprofile-null-1b3p5%7Eimjp489e%999k'
                },
                1459548811: {
                    'spiel': "Hi Paul,\nI'd like to join your LinkedIn network.\nSteven Blipvert\nPrincipal Test Architect and Agile Leader - Certified ScrumMaster\n",
                    'accept_url': 'https://www.linkedin.com/comm/people/invite-accept?mboxid=I6122153999904439999_500&sharedKey=-aWVMgrZ&fr=false&invitationId=6122153757099996400&fe=true&trk=eml-comm_invm-b-accept-newinvite&midToken=AQHQ1w999ws4wA&trkEmail=eml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%7Ejk',
                    'line_here': True,
                    'who': 'Steven Blipvert',
                    'img_src': 'https://media.licdn.com/mpr/mpr/shrinknp_100_100/p/4/000/17b/3db/1dbe948.jpg',
                    'profile_url': 'https://www.linkedin.com/comm/profile/view?id=AAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA&authType=name&authToken=F40O&invAcpt=2197625_I6122153999904439999_500&midToken=AQHQ1w999ws4wA&trk=eml-M2M_Invitation-hero-1-text%7Eprofile&trkEmail=eml-M2M_Invitation-hero-1-text%7Eprofile-null-1b3p5%7Eimjp489e%999k'
                }
            }),
            call.store_as_binary('most-recently-seen', 1459548811)])
        self.assertEquals(len(unmatched_to_move), 0)
        self.assertEquals(str(to_delete_from_notification_folder), "[1234, 1235]")
        self.assertEquals(len(final_invitations_store.invitations), 2)


INCOMING_1 = """From: Steven Footle <invitations@linkedin.com>
Message-ID: <997770868.3756094.1459635211566.JavaMail.app@lva1-app3333.prod.linkedin.com>
Subject: Paul, please add me to your LinkedIn network
MIME-Version: 1.0
Content-Type: multipart/alternative;
	boundary="----=_Part_3756092_595258213.1459635211563"
To: Paul Hammant <Paul@Hammant.org>
Date: Sat, 4 Apr 2016 22:13:31 +0000 (UTC)

------=_Part_3756092_595258213.1459635211563
Content-Type: text/plain;charset=UTF-8
Content-Transfer-Encoding: quoted-printable
Content-ID: text-body

Hi Paul,
I'd like to join your LinkedIn network.

Steven Footle
Principal Test Architect and Agile Leader - Certified ScrumMaster

Accept: https://www.linkedin.com/comm/people/invite-accept?mboxid=3DI612215=
3999904439999_500&sharedKey=3D-aWVMgrZ&fr=3Dfalse&invitationId=3D6122153757=
099996400&fe=3Dtrue&trk=3Deml-comm_invm-b-accept-newinvite&midToken=3DAQHQ1=
w999ws4wA&trkEmail=3Deml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%7=
Ejk

View Steven Footle's profile: https://www.linkedin.com/comm/profile/view?id=
=3DAAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA&authType=3Dname&authToken=3DF40O=
&invAcpt=3D2197625_I6122153999904439999_500&midToken=3DAQHQ1w999ws4wA&trk=
=3Deml-M2M_Invitation-hero-1-text%7Eprofile&trkEmail=3Deml-M2M_Invitation-h=
ero-1-text%7Eprofile-null-1b3p5%7Eimjp489e%999k

.....................................

Change frequency:: https://www.linkedin.com/e/v2?e=3D1b3p5-imjp489e-jk&t=3D=
lun&midToken=3DAQHQ1w999ws4wA&ek=3DM2M_Invitation&li=3D14&m=3Dunsub&ts=3Dfr=
eq&loid=3DAQGF11tOonwTvgAAAVPZCcz1nSHcTJlxFxG9A-VvJsBfOpDq9kyin-vZuBK5eK05u=
Pk1RDaz0lE&eid=3D1b3p5-imjp489e-jk

Unsubscribe:: https://www.linkedin.com/e/v2?e=3D1b3p5-imjp489e-jk&t=3Dlun&m=
idToken=3DAQHQ1w999ws4wA&ek=3DM2M_Invitation&li=3D13&m=3Dunsub&ts=3Dunsub&l=
oid=3DAQGGr0IzkTiBhAAAAVPZCcz1l3Sds05EdG8BZwq6RXOrd3bPZwuyMowSP7mYgnrv-VrYy=
3HNjss&eid=3D1b3p5-imjp489e-jk

Help:: https://www.linkedin.com/e/v2?e=3D1b3p5-imjp489e-jk&a=3DcustomerServ=
iceUrl&midToken=3DAQHQ1w999ws4wA&ek=3DM2M_Invitation&li=3D12&m=3Dfooter&ts=
=3Dhelp&articleId=3D67


You are receiving Invitation emails.

This email was intended for Paul Hammant (Senior Director of Engineering at=
 HedgeServ).
Learn why we included this: https://www.linkedin.com/e/v2?e=3D1b3p5-imjp489=
e-jk&a=3DcustomerServiceUrl&midToken=3DAQHQ1w999ws4wA&ek=3DM2M_Invitation&a=
rticleId=3D4788

=C2=A9 2016 LinkedIn Corporation, 2029 Stierlin Court, Mountain View CA 940=
43. LinkedIn and the LinkedIn logo are registered trademarks of LinkedIn.
------=_Part_3756092_595258213.1459635211563
Content-Type: text/html;charset=UTF-8
Content-Transfer-Encoding: quoted-printable
Content-ID: html-body

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.=
w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns=3D"http://www.w3=
.org/1999/xhtml"> <head> <meta http-equiv=3D"Content-Type" content=3D"text/=
html;charset=3Dutf-8"/> <meta name=3D"HandheldFriendly" content=3D"true"/> =
<meta name=3D"viewport" content=3D"width=3Ddevice-width; initial-scale=3D0.=
666667; maximum-scale=3D0.666667; user-scalable=3D0"/> <meta name=3D"viewpo=
rt" content=3D"width=3Ddevice-width"/> <title></title> <style type=3D"text/=
css">@media only screen and (max-width:512px) { .email-container { width:10=
0% !important; } } @media only screen and (max-width:320px) {} @media only =
screen and (max-device-width:480px) {} @media screen and (device-width:480p=
x) and (device-height:360px), screen and (device-width:360px) and (device-h=
eight:480px), screen and (device-width:320px) and (device-height:240px) {} =
@media screen and (-webkit-min-device-pixel-ratio:0) {} @media screen and (=
max-device-width:414px) and (max-device-height:776px) {} </style> </head> <=
body style=3D"background-color:#ECECEC;padding:0;margin:0;-webkit-text-size=
-adjust:100%;font-weight:200;width:100% !important;-ms-text-size-adjust:100=
%;"> <div style=3D"overflow:hidden;color:transparent;visibility:hidden;mso-=
hide:all;width:0;font-size:0;opacity:0;height:0;"> Hi Paul,&nbsp;I'd like t=
o join your LinkedIn network. </div> <table align=3D"center" border=3D"0" c=
ellspacing=3D"0" cellpadding=3D"0" style=3D"table-layout:fixed;-webkit-text=
-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;mso-table-lspace:0pt=
;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;" width=
=3D"100%"> <tbody> <tr> <td align=3D"center" style=3D"-webkit-text-size-adj=
ust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100=
%;"> <center style=3D"width:100%;"> <!--[if mso]><style type=3D"text/css">.=
email-container {width: 512px !important;}</style><![endif]--> <!--[if IE]>=
<style type=3D"text/css">.email-container {width: 512px !important;}</style=
><![endif]--> <table bgcolor=3D"#FFFFFF" border=3D"0" class=3D"email-contai=
ner" cellspacing=3D"0" cellpadding=3D"0" style=3D"margin:0 auto;max-width:5=
12px;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;wid=
th:inherit;mso-table-lspace:0pt;-ms-text-size-adjust:100%;font-family:Helve=
tica,Arial,sans-serif;" width=3D"512"> <tbody> <tr> <td bgcolor=3D"#F3F3F3"=
 width=3D"100%" style=3D"background-color:#F3F3F3;padding:12px;-webkit-text=
-size-adjust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-a=
djust:100%;border-bottom:1px solid #ECECEC;"> <table border=3D"0" cellspaci=
ng=3D"0" cellpadding=3D"0" style=3D"-webkit-text-size-adjust:100%;mso-table=
-rspace:0pt;font-weight:200;width:100% !important;mso-table-lspace:0pt;-ms-=
text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;min-width:100%=
 !important;" width=3D"100%"> <tbody> <tr> <td align=3D"left" valign=3D"mid=
dle" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-table-=
lspace:0pt;-ms-text-size-adjust:100%;"><a href=3D"https://www.linkedin.com/=
comm/nhome/?midToken=3DAQHQ1w999ws4wA&amp;trk=3Deml-M2M_Invitation-header-7=
-home&amp;trkEmail=3Deml-M2M_Invitation-header-7-home-null-1b3p5%7Eimjp489e=
%999k" style=3D"cursor:pointer;white-space:nowrap;-webkit-text-size-adjust:=
100%;display:inline-block;text-decoration:none;-ms-text-size-adjust:100%;">=
<img alt=3D"LinkedIn" border=3D"0" src=3D"https://static.licdn.com/scds/com=
mon/u/images/email/phoenix/logos/logo_phoenix_header_blue_78x66_v1.png" hei=
ght=3D"32" width=3D"38" style=3D"outline:none;-ms-interpolation-mode:bicubi=
c;color:#FFFFFF;text-indent:-999px;display:block;text-decoration:none;borde=
r-color:#ECECEC;border-width:1px;border-style:solid;"/></a></td> <td valign=
=3D"middle" width=3D"100%" align=3D"right" style=3D"padding:0 0 0 10px;-web=
kit-text-size-adjust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-tex=
t-size-adjust:100%;"><a href=3D"https://www.linkedin.com/comm/profile/view?=
id=3DAAsAAAAhiHkB2Xl5QqGw01CP-K2o5AvAA-e9my0&amp;midToken=3DAQHQ1w999ws4wA&=
amp;trk=3Deml-M2M_Invitation-header-15-profile&amp;trkEmail=3Deml-M2M_Invit=
ation-header-15-profile-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:pointer=
;margin:0;color:#4C4C4C;white-space:normal;-webkit-text-size-adjust:100%;di=
splay:inline-block;text-decoration:none;font-size:14px;-ms-text-size-adjust=
:100%;line-height:20px;">Paul Hammant</a></td> <td valign=3D"middle" width=
=3D"40" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;padding=
-left:10px;mso-table-lspace:0pt;-ms-text-size-adjust:100%;"><a href=3D"http=
s://www.linkedin.com/comm/profile/view?id=3DAAsAAAAhiHkB2Xl5QqGw01CP-K2o5Av=
AA-e9my0&amp;midToken=3DAQHQ1w999ws4wA&amp;trk=3Deml-M2M_Invitation-header-=
15-profile&amp;trkEmail=3Deml-M2M_Invitation-header-15-profile-null-1b3p5%7=
Eimjp489e%999k" style=3D"cursor:pointer;white-space:nowrap;-webkit-text-siz=
e-adjust:100%;display:inline-block;text-decoration:none;-ms-text-size-adjus=
t:100%;"><img alt=3D"Paul Hammant" border=3D"0" height=3D"32" src=3D"https:=
//media.licdn.com/mpr/mpr/shrinknp_100_100/p/6/005/095/3cc/24a8290.jpg" wid=
th=3D"32" style=3D"border-radius:50%;outline:none;-ms-interpolation-mode:bi=
cubic;color:#FFFFFF;text-indent:-999px;display:block;text-decoration:none;b=
order-color:#ECECEC;border-width:1px;border-style:solid;"/></a></td> <td wi=
dth=3D"1" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-t=
able-lspace:0pt;-ms-text-size-adjust:100%;">&nbsp;</td> </tr> </tbody> </ta=
ble></td> </tr> <tr> <td align=3D"left" style=3D"-webkit-text-size-adjust:1=
00%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;"> =
<table border=3D"0" cellspacing=3D"0" cellpadding=3D"0" style=3D"-webkit-te=
xt-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;mso-table-lspace:0=
pt;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;" width=
=3D"100%"> <tbody> <tr> <td width=3D"100%" style=3D"-webkit-text-size-adjus=
t:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;=
"> <table border=3D"0" cellspacing=3D"0" cellpadding=3D"0" style=3D"-webkit=
-text-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;mso-table-lspac=
e:0pt;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;" wi=
dth=3D"100%"> <tbody> <tr> <td width=3D"100%" style=3D"padding:24px;color:#=
434649;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-table-lspace:=
0pt;-ms-text-size-adjust:100%;"> <table bgcolor=3D"#FFFFFF" border=3D"0" ce=
llspacing=3D"0" cellpadding=3D"0" style=3D"-webkit-text-size-adjust:100%;ms=
o-table-rspace:0pt;font-weight:200;mso-table-lspace:0pt;-ms-text-size-adjus=
t:100%;font-family:Helvetica,Arial,sans-serif;" width=3D"100%"> <tbody> <tr=
> <td width=3D"100%" style=3D"padding:0 0 20px 0;-webkit-text-size-adjust:1=
00%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;"><=
h1 style=3D"padding:0;margin:0;font-weight:normal;padding-bottom:4px;font-s=
ize:20px;font-family:Helvetica Neue,Helvetica,Arial;line-height:24px;">Hi P=
aul,</h1><h2 style=3D"padding:0;margin:0;font-weight:normal;font-size:20px;=
font-family:Helvetica Neue,Helvetica,Arial;line-height:24px;">I'd like to j=
oin your LinkedIn network.</h2></td> </tr> <tr> <td style=3D"padding:0 0 20=
px 0;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-table-lspace:0p=
t;-ms-text-size-adjust:100%;"> <table border=3D"0" cellspacing=3D"0" cellpa=
dding=3D"0" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;fon=
t-weight:200;mso-table-lspace:0pt;-ms-text-size-adjust:100%;font-family:Hel=
vetica,Arial,sans-serif;" width=3D"100%"> <tbody> <tr> <td valign=3D"top" s=
tyle=3D"padding:0 15px 0 0;-webkit-text-size-adjust:100%;mso-table-rspace:0=
pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;"><a href=3D"https://www.=
linkedin.com/comm/profile/view?id=3DAAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA=
&amp;authType=3Dname&amp;authToken=3DF40O&amp;invAcpt=3D2197625_I6122153781=
204439999_500&amp;midToken=3DAQHQ1w999ws4wA&amp;trk=3Deml-M2M_Invitation-he=
ro-2-profile%7Epicture&amp;trkEmail=3Deml-M2M_Invitation-hero-2-profile%7Ep=
icture-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:pointer;white-space:nowr=
ap;-webkit-text-size-adjust:100%;display:inline-block;text-decoration:none;=
-ms-text-size-adjust:100%;"><img src=3D"https://media.licdn.com/mpr/mpr/shr=
inknp_100_100/p/4/000/17b/3db/1dbe948.jpg" alt=3D"Steven Footle" width=3D"84=
" height=3D"84" border=3D"0" style=3D"border-radius:50%;outline:none;-ms-in=
terpolation-mode:bicubic;color:#FFFFFF;text-indent:-999px;display:block;tex=
t-decoration:none;border-color:#ECECEC;border-width:1px;border-style:solid;=
"/></a></td> <td valign=3D"top" width=3D"100%" style=3D"-webkit-text-size-a=
djust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:1=
00%;"><a href=3D"https://www.linkedin.com/comm/profile/view?id=3DAAsAAAAIW1=
gBCVPJFcvlZjm6AtEfNiLTNya_HqA&amp;authType=3Dname&amp;authToken=3DF40O&amp;=
invAcpt=3D2197625_I6122153999904439999_500&amp;midToken=3DAQHQ1w999ws4wA&am=
p;trk=3Deml-M2M_Invitation-hero-4-profile%7Ename&amp;trkEmail=3Deml-M2M_Inv=
itation-hero-4-profile%7Ename-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:p=
ointer;white-space:nowrap;-webkit-text-size-adjust:100%;display:inline-bloc=
k;text-decoration:none;-ms-text-size-adjust:100%;"><h3 style=3D"padding:2px=
 0 4px 0;margin:0;color:#262626;font-weight:500;font-size:20px;font-family:=
Helvetica Neue,Helvetica,Arial;line-height:24px;">Steven Footle</h3></a><h3 =
style=3D"padding:0;margin:0;color:#737373;font-weight:normal;font-size:14px=
;font-family:Helvetica Neue,Helvetica,Arial;line-height:20px;">Principal Te=
st Architect and Agile Leader - Certified ScrumMaster</h3><h3 style=3D"padd=
ing:0;margin:0;color:#737373;font-weight:normal;font-size:14px;font-family:=
Helvetica Neue,Helvetica,Arial;line-height:20px;">Greater Boston Area</h3><=
/td> </tr> </tbody> </table></td> </tr> <tr> <td style=3D"-webkit-text-size=
-adjust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust=
:100%;"> <table border=3D"0" cellpadding=3D"0" cellspacing=3D"0" align=3D"c=
enter" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;font-wei=
ght:200;display:inline-block;mso-table-lspace:0pt;-ms-text-size-adjust:100%=
;"> <tbody> <tr> <td align=3D"center" valign=3D"middle" style=3D"padding:0 =
10px 10px 0;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-table-ls=
pace:0pt;font-size:16px;-ms-text-size-adjust:100%;"><a href=3D"https://www.=
linkedin.com/comm/profile/view?id=3DAAsAAAAIW1gBCVPJFcvlZjm6AtEfNiLTNya_HqA=
&amp;authType=3Dname&amp;authToken=3DF40O&amp;invAcpt=3D2197625_I6122153781=
204439999_500&amp;midToken=3DAQHQ1w999ws4wA&amp;trk=3Deml-M2M_Invitation-he=
ro-3-profile%7Etext&amp;trkEmail=3Deml-M2M_Invitation-hero-3-profile%7Etext=
-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:pointer;white-space:nowrap;-we=
bkit-text-size-adjust:100%;display:block;text-decoration:none;-ms-text-size=
-adjust:100%;"> <table border=3D"0" cellspacing=3D"0" cellpadding=3D"0" sty=
le=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;ms=
o-table-lspace:0pt;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sa=
ns-serif;" width=3D"100%"> <tbody> <tr> <td style=3D"cursor:pointer;border-=
radius:2px;padding:6px 16px;color:#737373;-webkit-text-size-adjust:100%;mso=
-table-rspace:0pt;mso-table-lspace:0pt;font-size:16px;-ms-text-size-adjust:=
100%;border-color:#737373;border-width:1px;border-style:solid;"><a href=3D"=
https://www.linkedin.com/comm/profile/view?id=3DAAsAAAAIW1gBCVPJFcvlZjm6AtE=
fNiLTNya_HqA&amp;authType=3Dname&amp;authToken=3DF40O&amp;invAcpt=3D2197625=
_I6122153999904439999_500&amp;midToken=3DAQHQ1w999ws4wA&amp;trk=3Deml-M2M_I=
nvitation-hero-3-profile%7Etext&amp;trkEmail=3Deml-M2M_Invitation-hero-3-pr=
ofile%7Etext-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:pointer;color:#737=
373;white-space:nowrap;-webkit-text-size-adjust:100%;display:block;text-dec=
oration:none;-ms-text-size-adjust:100%;">View profile</a></td> </tr> </tbod=
y> </table></a></td> </tr> </tbody> </table> <table border=3D"0" cellpaddin=
g=3D"0" cellspacing=3D"0" align=3D"center" style=3D"-webkit-text-size-adjus=
t:100%;mso-table-rspace:0pt;font-weight:200;display:inline-block;mso-table-=
lspace:0pt;-ms-text-size-adjust:100%;"> <tbody> <tr> <td align=3D"center" v=
align=3D"middle" style=3D"padding:0 10px 10px 0;-webkit-text-size-adjust:10=
0%;mso-table-rspace:0pt;mso-table-lspace:0pt;font-size:16px;-ms-text-size-a=
djust:100%;"><a href=3D"https://www.linkedin.com/comm/people/invite-accept?=
mboxid=3DI6122153999904439999_500&amp;sharedKey=3D-aWVMgrZ&amp;fr=3Dfalse&a=
mp;invitationId=3D6122153757099996400&amp;fe=3Dtrue&amp;trk=3Deml-comm_invm=
-b-accept-newinvite&amp;midToken=3DAQHQ1w999ws4wA&amp;trkEmail=3Deml-M2M_In=
vitation-null-5-null-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:pointer;wh=
ite-space:nowrap;-webkit-text-size-adjust:100%;display:block;text-decoratio=
n:none;-ms-text-size-adjust:100%;"> <table border=3D"0" cellspacing=3D"0" c=
ellpadding=3D"0" style=3D"-webkit-text-size-adjust:100%;mso-table-rspace:0p=
t;font-weight:200;mso-table-lspace:0pt;-ms-text-size-adjust:100%;font-famil=
y:Helvetica,Arial,sans-serif;" width=3D"100%"> <tbody> <tr> <td bgcolor=3D"=
#008CC9" style=3D"cursor:pointer;border-radius:2px;background-color:#008CC9=
;padding:6px 16px;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-ta=
ble-lspace:0pt;font-size:16px;-ms-text-size-adjust:100%;border-color:#008CC=
9;border-width:1px;border-style:solid;"><a href=3D"https://www.linkedin.com=
/comm/people/invite-accept?mboxid=3DI6122153999904439999_500&amp;sharedKey=
=3D-aWVMgrZ&amp;fr=3Dfalse&amp;invitationId=3D6122153757099996400&amp;fe=3D=
true&amp;trk=3Deml-comm_invm-b-accept-newinvite&amp;midToken=3DAQHQ1w999ws4=
wA&amp;trkEmail=3Deml-M2M_Invitation-null-5-null-null-1b3p5%7Eimjp489e%999k=
" style=3D"cursor:pointer;color:#FFFFFF;white-space:nowrap;-webkit-text-siz=
e-adjust:100%;display:block;text-decoration:none;-ms-text-size-adjust:100%;=
">Accept</a></td> </tr> </tbody> </table></a></td> </tr> </tbody> </table><=
/td> </tr> </tbody> </table></td> </tr> </tbody> </table></td> </tr> </tbod=
y> </table></td> </tr> <tr> <td align=3D"left" style=3D"-webkit-text-size-a=
djust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:1=
00%;"> <table bgcolor=3D"#ECECEC" border=3D"0" cellspacing=3D"0" cellpaddin=
g=3D"0" style=3D"padding:0 24px;color:#999999;-webkit-text-size-adjust:100%=
;mso-table-rspace:0pt;font-weight:200;mso-table-lspace:0pt;-ms-text-size-ad=
just:100%;font-family:Helvetica,Arial,sans-serif;" width=3D"100%"> <tbody> =
<tr> <td align=3D"center" width=3D"100%" style=3D"-webkit-text-size-adjust:=
100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;">=
 <table border=3D"0" cellspacing=3D"0" cellpadding=3D"0" style=3D"-webkit-t=
ext-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;mso-table-lspace:=
0pt;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;" widt=
h=3D"100%"> <tbody> <tr> <td align=3D"center" valign=3D"middle" width=3D"10=
0%" style=3D"border-top:1px solid #D9D9D9;padding:16px 0;-webkit-text-size-=
adjust:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:=
100%;text-align:center;"><a href=3D"https://www.linkedin.com/e/v2?e=3D1b3p5=
-imjp489e-jk&amp;t=3Dlun&amp;midToken=3DAQHQ1w999ws4wA&amp;ek=3DM2M_Invitat=
ion&amp;li=3D14&amp;m=3Dunsub&amp;ts=3Dfreq&amp;loid=3DAQGF11tOonwTvgAAAVPZ=
Ccz1nSHcTJlxFxG9A-VvJsBfOpDq9kyin-vZuBK5eK05uPk1RDaz0lE&amp;eid=3D1b3p5-imj=
p489e-jk" style=3D"cursor:pointer;color:#008CC9;white-space:nowrap;-webkit-=
text-size-adjust:100%;display:inline-block;text-decoration:none;font-size:1=
2px;-ms-text-size-adjust:100%;line-height:16px;">Change frequency</a>&nbsp;=
&nbsp;|&nbsp;&nbsp;<a href=3D"https://www.linkedin.com/e/v2?e=3D1b3p5-imjp4=
89e-jk&amp;t=3Dlun&amp;midToken=3DAQHQ1w999ws4wA&amp;ek=3DM2M_Invitation&am=
p;li=3D13&amp;m=3Dunsub&amp;ts=3Dunsub&amp;loid=3DAQGGr0IzkTiBhAAAAVPZCcz1l=
3Sds05EdG8BZwq6RXOrd3bPZwuyMowSP7mYgnrv-VrYy3HNjss&amp;eid=3D1b3p5-imjp489e=
-jk" style=3D"cursor:pointer;color:#008CC9;white-space:nowrap;-webkit-text-=
size-adjust:100%;display:inline-block;text-decoration:none;font-size:12px;-=
ms-text-size-adjust:100%;line-height:16px;">Unsubscribe</a>&nbsp;&nbsp;|&nb=
sp;&nbsp;<a href=3D"https://www.linkedin.com/e/v2?e=3D1b3p5-imjp489e-jk&amp=
;a=3DcustomerServiceUrl&amp;midToken=3DAQHQ1w999ws4wA&amp;ek=3DM2M_Invitati=
on&amp;li=3D12&amp;m=3Dfooter&amp;ts=3Dhelp&amp;articleId=3D67" style=3D"cu=
rsor:pointer;color:#008CC9;white-space:nowrap;-webkit-text-size-adjust:100%=
;display:inline-block;text-decoration:none;font-size:12px;-ms-text-size-adj=
ust:100%;line-height:16px;">Help</a></td> </tr> </tbody> </table></td> </tr=
> <tr> <td align=3D"center" width=3D"100%" style=3D"-webkit-text-size-adjus=
t:100%;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;=
"> <table border=3D"0" cellspacing=3D"0" cellpadding=3D"0" style=3D"-webkit=
-text-size-adjust:100%;mso-table-rspace:0pt;font-weight:200;mso-table-lspac=
e:0pt;-ms-text-size-adjust:100%;font-family:Helvetica,Arial,sans-serif;" wi=
dth=3D"100%"> <tbody> <tr> <td align=3D"center" width=3D"100%" style=3D"pad=
ding:0 0 12px 0;-webkit-text-size-adjust:100%;mso-table-rspace:0pt;mso-tabl=
e-lspace:0pt;font-size:12px;-ms-text-size-adjust:100%;line-height:16px;">Yo=
u are receiving Invitation emails.</td> </tr> <tr> <td align=3D"center" wid=
th=3D"100%" style=3D"padding:0 0 12px 0;-webkit-text-size-adjust:100%;mso-t=
able-rspace:0pt;mso-table-lspace:0pt;font-size:12px;-ms-text-size-adjust:10=
0%;line-height:16px;">This email was intended for Paul Hammant (Senior Dire=
ctor of Engineering at HedgeServ).&nbsp;<a href=3D"https://www.linkedin.com=
/e/v2?e=3D1b3p5-imjp489e-jk&amp;a=3DcustomerServiceUrl&amp;midToken=3DAQHQ1=
w999ws4wA&amp;ek=3DM2M_Invitation&amp;articleId=3D4788" style=3D"cursor:poi=
nter;color:#008CC9;white-space:nowrap;-webkit-text-size-adjust:100%;display=
:inline-block;text-decoration:none;-ms-text-size-adjust:100%;">Learn why we=
 included this.</a></td> </tr> </tbody> </table> <table border=3D"0" cellsp=
acing=3D"0" cellpadding=3D"0" style=3D"-webkit-text-size-adjust:100%;mso-ta=
ble-rspace:0pt;font-weight:200;mso-table-lspace:0pt;-ms-text-size-adjust:10=
0%;font-family:Helvetica,Arial,sans-serif;" width=3D"100%"> <tbody> <tr> <t=
d align=3D"center" style=3D"padding:0 0 8px 0;-webkit-text-size-adjust:100%=
;mso-table-rspace:0pt;mso-table-lspace:0pt;-ms-text-size-adjust:100%;" widt=
h=3D"100%"><a href=3D"https://www.linkedin.com/comm/nhome/?midToken=3DAQHQ1=
w999ws4wA&amp;trk=3Deml-M2M_Invitation-footer-11-home&amp;trkEmail=3Deml-M2=
M_Invitation-footer-11-home-null-1b3p5%7Eimjp489e%999k" style=3D"cursor:poi=
nter;white-space:nowrap;-webkit-text-size-adjust:100%;display:inline-block;=
text-decoration:none;-ms-text-size-adjust:100%;"><img alt=3D"LinkedIn" bord=
er=3D"0" height=3D"20" src=3D"https://static.licdn.com/scds/common/u/images=
/email/phoenix/logos/logo_phoenix_footer_gray_197x48_v1.png" width=3D"82" s=
tyle=3D"outline:none;-ms-interpolation-mode:bicubic;color:#FFFFFF;text-inde=
nt:-999px;display:block;text-decoration:none;border-color:#F3F3F3;border-wi=
dth:1px;border-style:solid;"/></a></td> </tr> <tr> <td align=3D"center" wid=
th=3D"100%" style=3D"padding:0 0 12px 0;-webkit-text-size-adjust:100%;mso-t=
able-rspace:0pt;mso-table-lspace:0pt;font-size:12px;-ms-text-size-adjust:10=
0%;line-height:16px;">&copy; 2016 LinkedIn Corporation, 2029 Stierlin Court=
, Mountain View CA 94043.&nbsp;LinkedIn and the LinkedIn logo are registere=
d trademarks of LinkedIn.</td> </tr> </tbody> </table></td> </tr> </tbody> =
</table></td> </tr> </tbody> </table> </center></td> </tr> </tbody> </table=
> <img src=3D"http://www.linkedin.com/emimp/1b3p5-imjp489e-jk.gif" style=3D=
"outline:none;-ms-interpolation-mode:bicubic;color:#FFFFFF;display:block;te=
xt-decoration:none;width:1px;border-color:#ECECEC;border-width:1px;border-s=
tyle:solid;height:1px;"/> </body> </html>
------=_Part_3756092_595258213.1459635211563--"""
