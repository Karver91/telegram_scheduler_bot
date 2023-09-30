from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний FSM
class FSMAddService(StatesGroup):
    """Класс машины состояний для добавления новой услуги в базу услуг"""
    service_name = State()
    service_duration = State()
    service_price = State()
    service_description = State()


class FSMRemoveService(StatesGroup):
    """Класс машины состояний для удаления услуги из базы услуг"""
    state_remove = State()


class FSMRecords(StatesGroup):
    """Класс машины состояний для работы с записью клиентов"""
    choice_service = State()
    choice_date = State()
    choice_time = State()
    choice_record = State()

