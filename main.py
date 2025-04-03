import asyncio
import logging
import random
import requests
import html
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher

# Конфигурация
TOKEN = "7510148360:AAES2DlYgidmUvFO-3lEXXvKowXuRtDdmNQ"
CHANNEL_ID = "@workskaz"
HH_URL = "https://api.hh.kz/vacancies"
CATEGORIES = {
    "1": "IT_интернет_телеком",
    "2": "Маркетинг_реклама_PR",
    "3": "Продажи",
    "4": "Транспорт_логистика",
    "5": "Строительство_недвижимость",
    "6": "Производство",
    "7": "Медицина_фармацевтика"
}  # Можно расширить до 10 категорий

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Фильтр по свежести вакансий (3 дня)
DAYS_FILTER = 3
DATE_FROM = (datetime.utcnow() - timedelta(days=DAYS_FILTER)).strftime('%Y-%m-%d')

async def fetch_vacancies(category_id):
    params = {
        "area": 160,  # Алматы
        "salary": 150000,
        "only_with_salary": True,
        "per_page": 50,  # Увеличиваем количество вакансий для каждой категории
        "professional_role": category_id,
        "date_from": DATE_FROM  # Только свежие вакансии
    }
    response = requests.get(HH_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("items", [])
    else:
        logging.error(f"Ошибка запроса: {response.status_code}")
        return []

async def send_vacancies():
    all_vacancies = []
    
    for category_id, category_name in CATEGORIES.items():
        vacancies = await fetch_vacancies(category_id)
        if vacancies:
            random.shuffle(vacancies)
            selected_vacancies = vacancies[:20]  # Выбираем 20 случайных вакансий
            all_vacancies.extend([(vacancy, category_name) for vacancy in selected_vacancies])
    
    for vacancy, category_name in all_vacancies:
        title = html.escape(vacancy["name"])
        salary = vacancy.get("salary", {}).get("from", "Не указана")
        url = vacancy["alternate_url"]
        employer = html.escape(vacancy["employer"]["name"])
        hashtag = f"#{category_name.replace(' ', '_')}"
        
        # Получение контактов
        contacts_info = ""
        if "contacts" in vacancy and vacancy["contacts"]:
            contacts = vacancy["contacts"]
            phones = contacts.get("phones", [])
            emails = contacts.get("email", [])
            
            contact_list = []
            for phone in phones:
                formatted_phone = phone.get("formatted", "")
                if formatted_phone:
                    contact_list.append(f"\U0001F4DE <b>Телефон:</b> {formatted_phone}")
            
            for email in emails:
                if email:
                    contact_list.append(f"\U0001F4E7 <b>Email:</b> {email}")
            
            if contact_list:
                contacts_info = "\n" + "\n".join(contact_list)
        
        text = (f"{hashtag}\n\U0001F4BC <b>{title}</b>\n\U0001F4B0 <b>Зарплата:</b> {salary} KZT\n"
                f"\U0001F3E2 <b>Компания:</b> {employer}\n"
                f"\U0001F4C1 <b>Категория:</b> {category_name}\n"
                f"{contacts_info}\n\n<a href='{url}'>Подробнее</a>")
        
        await bot.send_message(CHANNEL_ID, text, parse_mode="HTML", disable_web_page_preview=True)
    
async def scheduler():
    while True:
        await send_vacancies()
        await asyncio.sleep(21600)  # 6 часов

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
