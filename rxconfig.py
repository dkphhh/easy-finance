import os

import reflex as rx
from dotenv import load_dotenv

load_dotenv()

api_url = os.getenv("BACK_END")

config = rx.Config(
    app_name="easy_finance",
    loglevel="info",
    api_url=api_url,
    db_url="sqlite:///reflex.db",
    tailwind={
        "content": [
            "./app/**/*.py",
            "./app/**/*.js",
            "./app/**/*.html",
        ],
        "theme": {
            "extend": {},
        },
        "plugins": ["@tailwindcss/typography"],
    },
)
