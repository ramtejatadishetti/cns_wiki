import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

ADMIN_MAIL = ""
ADMIN_PASSWORD = ""
CERTIFICATE_STORE_PATH = "./certificates/"



def send_mail_from_admin(file_name, email_addr):
    msg = MIMEMultipart()
    msg['From'] = ADMIN_MAIL
    msg['To'] = email_addr
    msg['Subject'] = "CERTIFICATE FOR GNS"

    body = "Please use this certifcate for regisitering at GNS"

    msg.attach(MIMEText(body, 'plain'))

    complete_path = CERTIFICATE_STORE_PATH + file_name
    attachment = open(complete_path, "rb")

    part  = MIMEBase('application', 'octect-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(ADMIN_MAIL, ADMIN_PASSWORD)
    text = msg.as_string()
    server.sendmail(ADMIN_MAIL, email_addr, text)
    server.quit()


if __name__ == '__main__':
    send_mail_from_admin('certificate.crt', 'abc@gmail.com')
