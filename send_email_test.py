import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
sender_email = 'dianahsia0912@gmail.com'
receiver_email = 'ninghsia99912@gmail.com'
subject = 'New Review Posted'
body = 'New review has been posted.'

# Create the MIME object
message = MIMEMultipart()
message['From'] = sender_email
message['To'] = receiver_email
message['Subject'] = subject

# Attach the body to the email
message.attach(MIMEText(body, 'plain'))

# Set up the SMTP server
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'dianahsia0912@gmail.com'
smtp_password = 'nahm dstv ywtu rkio'

# Start the SMTP session
with smtplib.SMTP(smtp_server, smtp_port) as server:
    # Log in to the SMTP server
    server.starttls()
    server.login(smtp_username, smtp_password)

    # Send the email
    server.sendmail(sender_email, receiver_email, message.as_string())

print('Email sent successfully')
