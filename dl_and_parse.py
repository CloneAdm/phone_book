import os
import re
import json
import aiohttp
import asyncio
import argparse
import aiofiles
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass

from settings import URL, BASE_DIR, PHOTO_DIR, JSON_FILE, HTML_FILE
from settings import logger


@dataclass
class Contact:
    name: str
    company: str
    position: str
    department: str
    location: str
    birthday: str
    email: str
    phone_mobile: str
    phone_office: str
    photo_url: str
    photo_path: str | None = None


async def fetch_html(url: str) -> str:
    logger.debug(f"Получение HTML {url=} ...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            logger.debug(f"HTML получен {response.status=}")
            return await response.text()


async def fetch_photo(session: aiohttp.ClientSession, url: str, dest: Path) -> None:
    async with session.get(url) as response:
        response.raise_for_status()
        async with aiofiles.open(dest, 'wb') as f:
            await f.write(await response.read())
    logger.debug(f"Фотография сохранена {dest=}")


def update_photo_links(html: str, contacts: list[Contact]) -> str:
    logger.debug("Обновление ссылок на фотографии в HTML...")
    soup = BeautifulSoup(html, 'html.parser')
    for contact in contacts:
        if contact.photo_path:
            # Находим все img теги с соответствующим src атрибутом
            img_tags = soup.find_all('img', {'src': re.compile(re.escape(contact.photo_url) + r'(\?.*)?$')})
            for img_tag in img_tags:
                img_tag['src'] = contact.photo_path
    updated_html = str(soup)
    logger.debug("Ссылки на фотографии обновлены")
    return updated_html


async def download_photos(contacts: list[Contact]) -> None:
    logger.debug("Скачивание фотографий...")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for contact in contacts:
            photo_url = URL + contact.photo_url
            photo_path = PHOTO_DIR / Path(contact.photo_url).name
            contact.photo_path = str(photo_path)
            tasks.append(fetch_photo(session, photo_url, BASE_DIR / Path(photo_path)))
        await asyncio.gather(*tasks)


def parse_html(html: str) -> list[Contact]:
    logger.debug("Парсинг HTML...")
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select("div#MainContent_up > div.row")

    contacts = []
    for row in rows:
        cols = row.select('div.col-md-3 h5, div.col-md-3 h4, div.col-md-3 h6, div.col-md-1 h4, div.col-md-2 a, div.col-md-2 h4, div.col-md-2 img')

        photo_url = cols[0].get('src', '').strip()
        # Удаляем параметр кэш-обходчика
        photo_url = photo_url.split('?')[0]

        company = cols[1].text.strip()
        name = cols[2].text.strip()

        parts = [part.strip() for part in cols[3].text.strip().split(',')]
        department, position, location = parts

        birthday = cols[4].text.strip()
        email = cols[5].text.strip()
        phone_mobile = cols[7].text.strip()
        phone_office = cols[6].text.strip()

        contact = Contact(name=name,
                          company=company,
                          position=position,
                          department=department,
                          location=location,
                          birthday=birthday,
                          email=email,
                          phone_office=phone_office,
                          phone_mobile=phone_mobile,
                          photo_url=photo_url)
        contacts.append(contact)
    logger.debug(f"Парсинг HTML завершен. Количество контактов: {len(contacts)}")
    return contacts


async def main(args):
    logger.info("Запуск программы")
    try:
        if args.file:
            # Парсинг локального файла
            async with aiofiles.open(args.file, 'r', encoding='utf-8') as file:
                html = await file.read()
            logger.debug(f"HTML файл {args.file} прочитан")
        else:
            # Скачивание HTML по URL
            html = await fetch_html(URL)

        contacts: list[Contact] = parse_html(html)

        # Создание папок, если они не существуют
        os.makedirs(BASE_DIR / PHOTO_DIR, exist_ok=True)

        await download_photos(contacts)

        # Обновление HTML с новыми ссылками на фотографии и сохранение HTML с именем book_дата-время.html
        updated_html = update_photo_links(html, contacts)
        async with aiofiles.open(HTML_FILE, 'w', encoding='utf-8') as file:
            await file.write(updated_html)
        logger.info(f"HTML файл сохранен как {HTML_FILE}")

        # Сохранение данных в JSON
        async with aiofiles.open(JSON_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps([contact.__dict__ for contact in contacts], ensure_ascii=False, indent=4))
        logger.info(f"JSON файл сохранен как {JSON_FILE}")

        logger.info("Программа успешно завершена.")
    except Exception as e:
        logger.exception("Произошла ошибка")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Парсер HTML контактов')
    parser.add_argument('--file', type=str, help='Путь к локальному HTML файлу')
    main_args = parser.parse_args()
    asyncio.run(main(main_args))
