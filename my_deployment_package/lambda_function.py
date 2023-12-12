import json
# import mysql.connector
import pymysql
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def lambda_handler(event, context):
    return_body = ''
    try:
        connection = pymysql.connect(
            # host='database-1.cvlxq8ccnbut.us-east-1.rds.amazonaws.com',
            # port=3306,
            # user='admin',
            # password='Natalie3399!',
            # database='review'
            host='database-1.cc5bfbtbayuq.us-east-1.rds.amazonaws.com',
            port=3306,
            user='admin',
            password='dbuserdbuser',
            database='exampleDB'
        )

        cursor = connection.cursor()

        query = f"SELECT * FROM review WHERE notification = 0"
        cursor.execute(query)
        result = cursor.fetchall()

        # If there's new data, send an email
        if result:
            return_body = 'has new review'
            send_email(result)

            # Update notification column to 1 for processed records
            update_notification_query = f"UPDATE review SET notification = 1"
            cursor.execute(update_notification_query)
            connection.commit()
        else:
            return_body = 'no new review'

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if connection.ping(reconnect=True):
            cursor.close()
            connection.close()

    return {
        'statusCode': 200,
        'body': json.dumps(return_body)
    }


def send_email(data):
    try:

        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.ehlo()
        # server.starttls()
        # server.ehlo()
        # server.login("dianahsia0912@gmail.com", 'nahm dstv ywtu rkio')
        # msg = "test!!"
        # text = msg.as_string()
        # server.sendmail('dianahsia0912@gmail.com', 'ninghsia99912@gmail.com', text)

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
            server.ehlo()
            server.starttls()
            server.login(smtp_username, smtp_password)

            # Send the email
            server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as e:
        print("Error sending email:", e)
