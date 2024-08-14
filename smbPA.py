# https://github.com/streamlit/llm-examples/blob/main/Chatbot.py
# this project is a personal assistant for SMB's , it uses OpenAI API to generate responses to user input.
# to run use the following command: streamlit run smbPA.py


from openai import OpenAI
import streamlit as st
from streamlit_chat import message
import os
from dotenv import load_dotenv
from loguru import logger
import sys
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# os.system('pip install openai')


debug = False
debug_info = []
data = {}
msg_content = ""
im = Image.open("qulla.favicon.ico")
st.set_page_config(
    page_title="SMB Personal Assistant",
    page_icon=im,
    layout="wide",
)

load_dotenv()  # take environment variables from .env.
# openai_api_key = os.getenv("OPENAI_API_KEY")

# Check if running in Streamlit Cloud with st.secrets available
try:
    openai_api_key = st.secrets["openai_api_key"]
except:
    openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)


def send_email(subject, body, to="avimunk@gmail.com"):
    sender_email = "avimunk@gmail.com"
    sender_password = "jvna kqlc rrnu ruxv"

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to, text)
        server.quit()

        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def loggerInit():
    logger.remove()  # remove the default logger
    logger.add(sys.stdout, level="INFO")
    logger.add("logs/logfile.log", rotation="10 MB")  # Rotate the log file after it reaches 10 MB


loggerInit()


def openAIintrface(messages):
    logger.info("GPT session started openai caller")
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",
                                                  messages=messages,
                                                  temperature=0.7)

        total_tokens_used = response.usage.total_tokens
        total_tokens_used = f"Total token used: {total_tokens_used}"
        logger.info(total_tokens_used)
        return response.choices[0].message

    except Exception as e:
        logger.error("error in openai caller")
        logger.error(e)
        return {"role": "system", "content": "אני מצטער, אני לא יכול לעזור כרגע"}


with open("system_message.txt", "r", encoding="utf-8") as file:
    system_message = file.read()

# streamlit setup
# Inject custom CSS for RTL layout
st.markdown(
    """
    <style>
    /* Apply RTL direction to the entire Streamlit page */
    body {
        direction: rtl;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💬 שלום, אני הועזרת הוירטואלית של דניאל, איך אפשר לעזור? ")  # this sets the title of the page

if "messages" not in st.session_state:  # this is a streamlit feature that allows us to store data between runs, here is start it with the system message
    st.session_state["messages"] = [{"role": "system", "content": system_message}]

    try:
        client.chat.completions.create(model="gpt-4", messages=st.session_state.messages, temperature=0.1)
    except:
        print("error", openai_api_key)

with st.form("chat_input", clear_on_submit=True):
    user_input = st.text_input(
        label="Your message:",
        placeholder="",
        label_visibility="collapsed",
    )
    # Hidden submit button
    st.form_submit_button(label="שלח")

if user_input and openai_api_key:  # handle the user input and responses
    logger.info("receiving user input")
    logger.debug(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})  # add the user input to the messages
    message(user_input, is_user=True)

    response = openAIintrface(st.session_state.messages)  # call OpenAI with all the messages
    logger.info( response.content)
    msg_content = response.content

    # Check if the response starts with '@' and remove it
    try:
        if msg_content.startswith('@'):
            logger.info("Response starts with '@', removing '@' characters")
            msg_content = msg_content.lstrip('@')  # Remove leading '@' characters
            # Send an email with the cleaned message
            send_email(
                subject="New Message from your PDA",
                body=f"Here is the cleaned message that was sent to the user:\n\n{msg_content}")
            msg_content = ""
    except:
        pass
    if msg_content.startswith('@'):
        logger.info("Response starts with '@', removing '@' characters")
        msg_content = msg_content.lstrip('@')  # Remove leading '@' characters
        # Send an email with the cleaned message
        send_email(
            subject="New Message from your PDA",
            body=f"Here is the cleaned message that was sent to the user:\n\n{msg_content}")
        msg_content = ""

    st.session_state.messages.append({"role": "assistant", "content": msg_content})  # Add the modified message
    message(msg_content)  # Display the modified message
