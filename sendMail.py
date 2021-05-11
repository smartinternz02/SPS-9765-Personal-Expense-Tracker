import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
load_dotenv()

def sendMail(user_mail,msg):
    message = Mail(from_email='kavitashegde4@gmail.com',
    to_emails=user_mail,
    subject='Max Expendituer Limit Reached',
    plain_text_content='and easy to access',
    html_content=msg)

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)



    