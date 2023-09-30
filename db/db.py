import aiomysql
from asyncio import Lock
from config_data.config import DATABASE, DB_HOST, DB_USER, DB_PASSWORD


class Database:
    def __init__(self):
        self.user: str = DB_USER
        self.password: str = DB_PASSWORD
        self.host: str = DB_HOST
        self.database: str = DATABASE
        self.port: int = 3306
        self.connection: aiomysql.Connection | None = None
        self.cursor: aiomysql.Cursor | None = None
        self._lock: Lock = Lock()  # Будет блокировать потоки при вызове execute

    async def __execute(self, query: str, values: tuple = None, commit: bool = False):
        """Выполняет работу с БД"""
        async with self._lock:
            await self.__connect()
            await self.cursor.execute(query, values)
            if commit:
                await self.connection.commit()

    async def __connect(self):
        """Устанавливает соединение"""
        if self.connection is None:
            self.connection: aiomysql.Connection = await aiomysql.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
        self.cursor: aiomysql.Cursor = await self.connection.cursor(aiomysql.DictCursor)

    async def __close(self) -> None:
        """Закрывает соединение"""
        if isinstance(self.connection, aiomysql.Connection):
            await self.cursor.close()
            self.connection.close()
            self.connection = None
            self.cursor = None

    async def create_tables(self):
        """Создает Базу Данных"""
        await self.__execute(query=f"CREATE DATABASE IF NOT EXISTS {self.database};\n"
                                   f"CREATE TABLE IF NOT EXISTS {self.database}.services("
                                   f"service_name VARCHAR(32) UNIQUE, "
                                   f"description VARCHAR(500), "
                                   f"duration TINYINT, "
                                   f"price SMALLINT"
                                   f");\n"
                                   f"CREATE TABLE IF NOT EXISTS {self.database}.working_hours("
                                   f"time TIME UNIQUE"
                                   f");\n"
                                   f"CREATE TABLE IF NOT EXISTS {self.database}.schedule("
                                   f"user_id BIGINT NOT NULL, "
                                   f"service_name VARCHAR(32), "
                                   f"date DATE, "
                                   f"time TIME"
                                   f");"
                             )
        await self.__close()

    async def add_working_hours(self):
        """Добавляет рабочие часы в базу"""
        hours = ('090000', '093000', '100000', '103000', '110000', '113000', '120000', '123000', '140000', '143000',
                 '150000', '153000', '160000', '163000', '170000', '173000')
        for hour in hours:
            await self.__execute(query=f"INSERT INTO {self.database}.working_hours (time) "
                                       f"VALUES (%s)"
                                       f"ON DUPLICATE KEY UPDATE time = {hour}",
                                 values=(hour,),
                                 commit=True)
        await self.__close()

    async def get_working_hours(self):
        """Получает рабочие часы из базы"""
        await self.__execute(query=f"SELECT * FROM {self.database}.working_hours")
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def add_record_to_schedule(self, user_id, service_name, date, time):
        """Добавляем новую запись в расписание"""
        await self.__execute(query=f"INSERT INTO {self.database}.schedule (user_id, service_name, date, time) "
                                   f"VALUES (%s, %s, %s, %s)",
                             values=(user_id, service_name, date, time),
                             commit=True)
        await self.__close()

    async def delete_old_records(self):
        await self.__execute(query=f"DELETE FROM {self.database}.schedule WHERE date < NOW() - INTERVAL 1 DAY",
                             commit=True)

    async def delete_record(self, date, time):
        await self.__execute(query=f"DELETE FROM {self.database}.schedule WHERE date = %s AND time = %s",
                             values=(date, time),
                             commit=True)

    # ------------------------------------------------------------------------------------------------------------------
    async def get_time_and_duration_for_date_from_schedule(self, date):
        await self.__execute(query=f"SELECT time, duration FROM {self.database}.schedule, {self.database}.services WHERE "
                             f"{self.database}.schedule.service_name = {self.database}.services.service_name AND "
                             f"{self.database}.schedule.date = (%s)",
                             values=(date, ))
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def get_record_by_date_and_time(self, date, time):
        """Получает записи из расписания по дате и времени"""
        await self.__execute(query=f"SELECT * FROM {self.database}.schedule WHERE date = %s AND time = %s",
                             values=(date, time))
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def get_record_by_user_id(self, user_id):
        """Получает запись клиента на услугу по его id"""
        await self.__execute(query=f"SELECT service_name, date, time FROM {self.database}.schedule WHERE user_id = %s",
                             values=user_id)
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def get_all_records_from_schedule(self):
        """Получает все записи из schedule"""
        await self.__execute(query=f"SELECT service_name, date, time FROM {self.database}.schedule")
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    # ------------------------------------------------------------------------------------------------------------------

    async def get_schedule_for_date_from_db(self, date):
        """Получаем расписание из базы"""
        await self.__execute(query=f"SELECT * FROM {self.database}.schedule WHERE date = %s",
                             values=date)
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def add_service_to_db(self, service):
        """Добавляет новую услугу в базу услуг"""
        await self.__execute(query=f"INSERT INTO {self.database}.services (service_name, description, duration, price) "
                                   f"VALUES (%s, %s, %s, %s) "
                                   f"ON DUPLICATE KEY UPDATE `service_name` = '{service['name']}'",
                             values=(service['name'], service['description'], service['duration'], service['price']),
                             commit=True)
        await self.__close()

    async def remove_service_from_db(self, service_name):
        """Удаляет услугу из базы услуг"""
        await self.__execute(query=f"DELETE FROM {self.database}.services WHERE service_name = %s",
                             values=service_name,
                             commit=True)
        await self.__close()

    async def get_services_from_db(self):
        """Получает все услуги из базы услуг"""
        await self.__execute(query=f"SELECT * FROM {self.database}.services")
        result = await self.cursor.fetchall()
        await self.__close()
        return result

    async def get_service_description_from_db(self, service_name):
        """Получает услугу из базы и ее описание"""
        await self.__execute(query=f"SELECT * FROM {self.database}.services WHERE service_name = %s",
                             values=service_name)
        result = await self.cursor.fetchone()
        await self.__close()
        return result


database = Database()
