from flask import Flask, request
import telebot
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions

# API Keys များကို Vercel Environment Variables ကနေ ဆွဲယူမည်
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# /start Command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ကြိုဆိုပါတယ်။ ရုပ်ရှင်အကြောင်း သိချင်ရင် ရုပ်ရှင်နာမည် ရိုက်ရှာနိုင်ပါတယ်။")

# ရုပ်ရှင်ရှာဖွေသည့် အပိုင်း
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    movie_name = message.text
    try:
        # ၁။ ရုပ်ရှင် ရှာဖွေခြင်း
        search_url = "https://api.themoviedb.org/3/search/movie"
        search_params = {'api_key': TMDB_API_KEY, 'query': movie_name, 'language': 'en-US'}
        search_response = requests.get(search_url, params=search_params).json()
        results = search_response.get('results', [])
        
        if not results:
            bot.reply_to(message, "ရုပ်ရှင် ရှာမတွေ့ပါဘူး ခင်ဗျာ။")
            return
            
        movie = results[0]
        movie_id = movie.get('id')
        title = movie.get('title')
        release_date = movie.get('release_date', 'N/A')
        year = release_date.split('-')[0] if release_date else 'N/A'
        rating = movie.get('vote_average', 'N/A')
        overview = movie.get('overview', 'No summary available.')
        poster_path = movie.get('poster_path')
        
        # ၂။ Trailer ရှာဖွေခြင်း
        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
        video_response = requests.get(video_url, params={'api_key': TMDB_API_KEY, 'language': 'en-US'}).json()
        video_results = video_response.get('results', [])
        
        trailer_link = ""
        for video in video_results:
            if video.get('site') == 'YouTube' and video.get('type') in ['Trailer', 'Teaser']:
                trailer_link = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
        
        # ၃။ Message စာသား ပြင်ဆင်ခြင်း
        reply_message = f"🎬 *{title}* ({year})\n⭐️ Rating: {rating}/10\n\n📝 *Summary:*\n{overview}\n\n"
        
        # Inline Keyboard ခလုတ်ဆောက်ခြင်း
        markup = InlineKeyboardMarkup()
        
        if trailer_link:
            reply_message += f"📺 *Official Trailer:* {trailer_link}"
            # စာသားအောက်မှာ နှိပ်လို့ရမယ့် ခလုတ်လှလှလေး ထည့်ပေးခြင်း
            markup.add(InlineKeyboardButton(text="📺 Watch Trailer", url=trailer_link))
        else:
            reply_message += "📺 *Trailer:* Not available."

        # Telegram In-app Video Player ပွင့်စေရန် Setting သတ်မှတ်ခြင်း
        preview_options = LinkPreviewOptions(is_disabled=False, prefer_large_media=True)

        # ၄။ User ထံ ပုံနှင့်စာ တွဲပို့ခြင်း
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            # ပုံနဲ့တွဲပို့ရင် Caption အောက်မှာ ခလုတ်ပေါ်လာပါမယ်
            bot.send_photo(
                message.chat.id, 
                poster_url, 
                caption=reply_message, 
                parse_mode='Markdown', 
                reply_markup=markup
            )
        else:
            # ပုံမရှိရင် စာချည်းပဲပို့ပြီး YouTube Player ပေါ်အောင်လုပ်ပါမယ်
            bot.send_message(
                message.chat.id, 
                reply_message, 
                parse_mode='Markdown', 
                reply_markup=markup,
                link_preview_options=preview_options
            )
            
    except Exception as e:
        print(e)
        bot.reply_to(message, "အမှားအယွင်းတစ်ခု ရှိသွားပါတယ်။")

# Vercel က လှမ်းခေါ်မယ့် Webhook Route
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

@app.route('/', methods=['GET'])
def index():
    return "Bot is running...", 200
    
