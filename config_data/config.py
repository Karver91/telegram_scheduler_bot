from environs import Env

# Экземпляр класса Env для обращения к переменным окружения
env: Env = Env()
env.read_env()

# BOT
BOT_TOKEN = env.str('BOT_TOKEN')
ADMIN_IDS = set(map(int, env.list('ADMIN_IDS')))

# DATABASE
DATABASE = env.str('DATABASE')
DB_HOST = env.str('DB_HOST')
DB_USER = env.str('DB_USER')
DB_PASSWORD = env.str('DB_PASSWORD')

MONTH_LIMIT = env.int('MONTH_LIMIT')
WEEKEND = tuple(map(int, env.list('WEEKEND')))

# CONTACT DETAILS
SALON_ADDRESS = env.str('SALON_ADDRESS')
SALON_PHONE = env.str('SALON_PHONE')
