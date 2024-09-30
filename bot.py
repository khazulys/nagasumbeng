import telebot
import os
import time
import requests
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv
from telebot import types
from googlesearch import search
from urllib.parse import urlparse
from keep_alive import keep_alive

load_dotenv()

keep_alive()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Dictionary untuk menyimpan state data sementara per pengguna
user_data = {}

PASSWORD = 'catchmeifyoucan1337""'  # Password yang benar
BASE_URL = 'https://pkp.sfu.ca/software/ojs/download/archive/'

# Function untuk fetch konten dari URL
def fetch_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return bs(response.text, 'html.parser')
    except requests.RequestException as e:
        return None

# Function untuk mendapatkan daftar versi OJS
def get_version_list():
    soup = fetch_content(BASE_URL)
    if soup:
        return [element.get_text(strip=True) for element in soup.find_all('h2')]
    return []

# Function untuk mendapatkan data versi OJS
def get_ojs_version_data():
    soup = fetch_content(BASE_URL)
    if soup:
        return soup.find_all('td')
    return []

# Function untuk menampilkan daftar versi OJS dengan link rilis
def display_filtered_versions(version_string):
    html_list = get_ojs_version_data()
    result = []
    for i in range(0, len(html_list), 3):
        date_element = html_list[i].get_text(strip=True)
        link_element = html_list[i + 1].find('a')

        if link_element and version_string in link_element.get_text():
            result.append((date_element, link_element['href']))

    return result

# Function untuk menampilkan daftar versi lama OJS
def display_old_versions(version_keyword):
    soup = fetch_content(BASE_URL)
    if soup:
        links = [
            link['href'] for link in soup.find_all('a')
            if link.has_attr('href') and version_keyword in link['href'].lower()
        ]
        return links
    return []

# Handler untuk perintah /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, 'Hey, passwordnya abangkuhh?')

    # Simpan state bahwa user harus memasukkan password
    user_data[chat_id] = {'authenticated': False}
    bot.register_next_step_handler(message, check_password)

# Handler untuk perintah /listojs
@bot.message_handler(commands=['listojs'])
def list_ojs(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    version_list = get_version_list()
    if version_list:
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        for version in version_list:
            # Membuat tombol inline untuk setiap versi OJS
            markup.add(types.InlineKeyboardButton(version, callback_data=version))
        
        bot.send_message(chat_id, "Pilih versi OJS yang ingin ditampilkan:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Gagal mengambil daftar versi OJS.")

# Callback query handler untuk pilihan versi OJS
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    version = call.data
    chat_id = call.message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    # Mapping versi OJS dengan string yang cocok untuk pencarian
    version_mapping = {
        'OJS 3.4': '3.4',
        'OJS 3.3': '3.3',
        'OJS 3.2': '3.2',
        'OJS 3.1': '3.1',
        'OJS 3.0': '3.0',
        'OJS 2.X': 'ojs-2',
        'OJS 1.X': 'ojs-1',
    }

    if version in version_mapping:
        # Menampilkan versi lama atau versi terbaru sesuai pilihan
        if 'OJS 2.X' in version or 'OJS 1.X' in version:
            links = display_old_versions(version_mapping[version])
            if links:
                for link in links:
                    bot.send_message(chat_id, f"Link: {link}")
            else:
                bot.send_message(chat_id, f"Tidak ditemukan versi OJS untuk {version}")
        else:
            filtered_versions = display_filtered_versions(version_mapping[version])
            if filtered_versions:
                for date, link in filtered_versions:
                    bot.send_message(chat_id, f"Tanggal Rilis: {date}\nLink: {link}")
            else:
                bot.send_message(chat_id, f"Tidak ditemukan versi OJS untuk {version}")
    else:
        bot.send_message(chat_id, "Versi tidak ditemukan.")

# Fungsi untuk memeriksa password
def check_password(message):
    chat_id = message.chat.id
    password = message.text.strip()

    if password.lower() == PASSWORD:
        # Jika password benar, update state dan tampilkan menu
        user_data[chat_id]['authenticated'] = True
        bot.send_message(chat_id, 'Yeayy password benar! kamu adalah BOSS, kamu dapat mengakses fitur bot.', reply_markup=inlinekey())
    else:
        # Jika password salah, minta ulang
        bot.send_chat_action(chat_id, 'typing')
        bot.send_message(chat_id, 'Password salah, anjing. dasar babu!')
        bot.register_next_step_handler(message, check_password)

# create inline keyboard button
def inlinekey():
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn1 = types.KeyboardButton('Dorking OJS')
    btn2 = types.KeyboardButton('Cek No WA')
    btn3 = types.KeyboardButton('Auto Schedule IG')
    markup.add(btn1, btn2, btn3)
    
    return markup

# Handler untuk fitur bot yang hanya dapat diakses jika sudah autentikasi
@bot.message_handler(func=lambda message: message.text == 'Dorking OJS' or message.text == 'Cek No WA' or message.text == 'Auto Schedule IG')
def feature_access(message):
    chat_id = message.chat.id
    
    # Cek apakah 'authenticated' ada sebelum mengakses
    if chat_id in user_data and user_data[chat_id].get('authenticated', False):
        if message.text == 'Dorking OJS':
            handler_dorking_ojs(message)
        elif message.text == 'Cek No WA':
            handler_check_wa(message)
        elif message.text == 'Auto Schedule IG':
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "Fitur Auto Schedule IG belum diimplementasikan.")
    else:
        bot.send_chat_action(chat_id, 'typing')
        bot.send_message(chat_id, 'Kamu belum memasukkan password yang benar abangkuh. Silakan mulai ulang dengan mengetik /start.')

# create function dorking ojs
def google_search(query, num_pages):
    search_results = set()
    domains_seen = set()
    
    for result in search(query, num_results=num_pages * 2):
        domain = urlparse(result).netloc
        
        if domain not in domains_seen:
            search_results.add(result)
            domains_seen.add(domain)
            if len(search_results) >= num_pages:
                break
            
    return list(search_results)

def save_to_file(data, filename):
    with open(filename, 'a') as file: 
        for item in data:
            file.write(f"{item}\n")

# create function check whatsapp number
def check_whatsapp_number(number):
    url = "https://gate.whapi.cloud/contacts"
    payload = {
        "blocking": "no_wait",
        "force_check": False,
        "contacts": [str(number)]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer XP2qTuLLuSRGXwgpbO3zfsn5Hxh6JHNP"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Handler untuk fitur "Dorking OJS"
@bot.message_handler(func=lambda message: message.text=='Dorking OJS')
def handler_dorking_ojs(message):
    chat_id = message.chat.id
    
    bot.send_chat_action(chat_id, 'typing')
    bot.reply_to(message, 'Masukkan beberapa domain dipisahkan dengan koma (misal: net, ac.id, com)')
    
    bot.register_next_step_handler(message, process_domains)

def process_domains(message):
    chat_id = message.chat.id
    domains = message.text.split(',')
    cleaned_domains = [domain.strip() for domain in domains]
    
    # Perbarui data pengguna tanpa menimpa data yang sudah ada
    user_data[chat_id].update({'domains': cleaned_domains})
    
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, 'Masukkan versi OJS yang ingin dicari (misal: 18.0.8)')
    
    bot.register_next_step_handler(message, process_ojs_version)

def process_ojs_version(message):
    chat_id = message.chat.id
    ojs_version = message.text.strip()
    
    # Pastikan kunci 'domains' ada di user_data
    if chat_id in user_data and 'domains' in user_data[chat_id]:
        # Perbarui data pengguna tanpa menimpa data lain
        user_data[chat_id].update({'ojs_version': ojs_version})
        
        num_results_per_domain = 15
        domains = user_data[chat_id]['domains']
        
        bot.send_chat_action(chat_id, 'typing')
        bot.send_message(chat_id, 'Mohon tunggu, sedang proses pencarian')
                
        for site in domains:
            site = site.strip()
            query = f'site:{site} inurl:about/aboutThisPublishingSystem "Open Journal Systems" "{ojs_version}"'
            
            # Mengambil hasil pencarian
            results = google_search(query, num_results_per_domain)
            
            if results:
                # Kirim setiap hasil pencarian sebagai pesan terpisah
                save_to_file(results, 'ojs.txt')
                    
            else:
                bot.send_message(chat_id, f"Tidak ada hasil yang ditemukan untuk domain: {site}\n")
            
        bot.send_chat_action(chat_id, 'upload_document')
        with open('ojs.txt', 'rb') as file:
            bot.send_document(chat_id, file, caption='Berikut adalah hasil dorking ojs.')
        os.remove('ojs.txt')
    else:
        bot.send_chat_action(chat_id, 'typing')
        bot.send_message(chat_id, 'Terjadi kesalahan. Silakan mulai ulang dengan mengetik /start.')

# Handler untuk fitur "Cek No WA"
@bot.message_handler(func=lambda message: message.text=='Cek No WA')
def handler_check_wa(message):
    chat_id = message.chat.id
    
    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, "Silakan kirimkan file teks yang berisi daftar nomor Handhone.\n\nNote : format no.hp dalam file harus 62812xxx")
    
    bot.register_next_step_handler(message, receive_file)
    
# Handler untuk menerima file teks berisi daftar nomor HP
def receive_file(message):
    chat_id = message.chat.id
    
    if message.document:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open('nomor_hp.txt', 'wb') as new_file:
            new_file.write(downloaded_file)
        
        with open('nomor_hp.txt', 'r') as file:
            phone_numbers = [line.strip() for line in file.readlines()]
        
        os.remove('nomor_hp.txt')  # Hapus file setelah diproses
        
        # Mulai proses pengecekan nomor WhatsApp
        bot.send_chat_action(chat_id, 'typing')
        bot.send_message(chat_id, 'Sedang memproses pengecekan nomor WhatsApp, mohon tunggu...')
        
        results = []
        for number in phone_numbers:
            response = check_whatsapp_number(number)
            if response.get('contacts'):
                status = response['contacts'][0].get('status')
                results.append(f"Nomor: {number} - Status: {status}")
            else:
                results.append(f"Nomor: {number} - Tidak ditemukan atau tidak valid.")
        
        # Kirim hasil pengecekan ke user
        result_text = '\n'.join(results)
        bot.send_message(chat_id, f"Hasil pengecekan:\n{result_text}")
    else:
        bot.send_message(chat_id, "File yang dikirim bukan teks. Silakan kirim file teks yang berisi daftar nomor HP dengan format yang benar.")

# Fungsi untuk menjalankan bot
def main():
    while True:
        try:
            print("Bot berjalan...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
