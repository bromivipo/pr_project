from tg_token import TOKEN
from db_class import Data
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

API = TOKEN
HELP = '''/start - начать работу
/help - список функций
/register -  зарегистрироваться
/set_deadline - назначить личный дедлайн
/check_deadlines - посмотреть все свои невыполненые задачи
/check_upcoming_deadlines - посмотреть все свои предстоящие невыполненные задачи
/deadline_done - поменять статус дедлайна на DONE
/delete_deadline - удалить дедлайн
'''
STORAGE = MemoryStorage()
bot = Bot(API)
dispatcher = Dispatcher(bot, storage=STORAGE)

connection = sqlite3.connect("data.db")
db = Data(connection)

class Reg(StatesGroup):
    login = State()
    password = State()


class PersonalDeadline(StatesGroup):
    name = State()
    description = State()
    deadline = State()


class CreateProject(StatesGroup):
    name = State()
    description = State()
    login_list = State()


@dispatcher.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.answer(text=HELP)
    await message.delete()


@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(text='Бот подключен! Чтобы узнать, что он умеет, напишите /help')




@dispatcher.message_handler(commands=['register'])
async def register(message: types.Message):
    await message.answer(text='Введите логин')
    await Reg.login.set()


@dispatcher.message_handler(state=Reg.login)
async def register_login(message: types.Message, state: FSMContext):
    await message.answer(text='Введите пароль')
    await state.update_data(login=message.text)
    await Reg.password.set()


@dispatcher.message_handler(state=Reg.password)
async def register_pass(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    res = db.add_user(message.from_user.id, data['login'], data['password'])
    if res == 1:
        await message.answer("Вы успешно зарегистрированы!")
    elif res == 0:
        await message.answer("Ошибка при регистрации! Такой логин уже существует, выберите новый!")
    else:
        await message.answer("Ошибка при регистрации! К вашему telegram_id уже привязан аккаунт")
    await state.finish()
   


@dispatcher.message_handler(commands=['set_deadline'])
async def set_deadline(message: types.Message):
    await message.answer(text='Введите название задачи')
    await PersonalDeadline.name.set()


@dispatcher.message_handler(state=PersonalDeadline.name)
async def set_deadline_name(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите описание задачи')
    await state.update_data(name=message.text)
    await PersonalDeadline.description.set()


@dispatcher.message_handler(state=PersonalDeadline.description)
async def set_deadline_description(message: types.Message, state: FSMContext):
    await message.answer(text='Задайте дедлайн в формате dd/mm/yyyy hh:mi:ss')
    await state.update_data(description=message.text)
    await PersonalDeadline.deadline.set()


@dispatcher.message_handler(state=PersonalDeadline.deadline)
async def set_deadline_date(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    data = await state.get_data()
    db.add_personal(message.from_user.id, data['name'], data['description'], data['deadline'])
    await message.answer(f"Название: {data['name']}\n"
                         f"Описание: {data['description']}\n"
                         f"Дедлайн: {data['deadline']}")
    await state.finish()




@dispatcher.message_handler(commands=['create_project'])
async def create_project(message: types.Message):
    await message.answer(text='Введите название проекта')
    await CreateProject.name.set()


@dispatcher.message_handler(state=CreateProject.name)
async def create_project_name(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите описание проекта')
    await state.update_data(name=message.text)
    await CreateProject.description.set()


@dispatcher.message_handler(state=CreateProject.description)
async def create_project_description(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите логины участников проекта(свой логин не указывайте) по одному в сообщении. Когда вы добавите всех напишите "Стоп"')
    await state.update_data(description=message.text)
    await state.update_data(login_list=[])
    await CreateProject.login_list.set()


@dispatcher.message_handler(state=CreateProject.login_list)
async def create_project_logins(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text.lower() != "стоп":
        data['login_list'].append(message.text)
        await state.update_data(login_list=data['login_list'])
        await message.answer(text="Введите следующий логин")
    else:
        await message.answer(text=data["login_list"])
        await state.finish()



class ProjectDeadline(StatesGroup):
    project_name = State()
    task_name = State()
    description = State()
    login = State()
    deadline = State()


@dispatcher.message_handler(commands=['set_project_deadline'])
async def set_project_deadline(message: types.Message):
    await message.answer(text='Введите название проекта')
    await ProjectDeadline.project_name.set()


@dispatcher.message_handler(state=ProjectDeadline.project_name)
async def set_deadline_project_name(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите название задачи')
    await state.update_data(project_name=message.text)
    await ProjectDeadline.task_name.set()


@dispatcher.message_handler(state=ProjectDeadline.task_name)
async def set_deadline_project_task_name(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите описание задачи')
    await state.update_data(task_name=message.text)
    await ProjectDeadline.description.set()


@dispatcher.message_handler(state=ProjectDeadline.description)
async def set_deadline_project_description(message: types.Message, state: FSMContext):
    await message.answer(text='Укажите логин участника, которому будет назначена задача ')
    await state.update_data(description=message.text)
    await ProjectDeadline.login.set()


@dispatcher.message_handler(state=ProjectDeadline.login)
async def set_deadline_project_login(message: types.Message, state: FSMContext):
    await message.answer(text='Задайте дедлайн в формате dd.mm.yyyy')
    await state.update_data(login=message.text)
    await ProjectDeadline.deadline.set()


@dispatcher.message_handler(state=ProjectDeadline.deadline)
async def set_deadline_project_date(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    data = await state.get_data()
    await message.answer(f"Название проекта: {data['project_name']}\n"
                         f"Название задачи: {data['task_name']}\n"
                         f"Описание: {data['description']}\n"
                         f"Логин: {data['login']}\n"
                         f"Дедлайн: {data['deadline']}")
    await state.finish()



@dispatcher.message_handler(commands=['check_deadlines'])
async def check_deadline(message: types.Message):
    res = db.get_deadlines(message.from_user.id)
    if res:
        await message.answer(text=f'Вот ваши дедлайны: {res}')
    else:
        await message.answer(text=f'У вас нет дедлайнов')

@dispatcher.message_handler(commands=['check_upcoming_deadlines'])
async def check_upcoming_deadline(message: types.Message):
    res = db.get_upcoming_deadlines(message.from_user.id)
    if res:
        await message.answer(text=f'Вот ваши предстоящие дедлайны: {res}')
    else:
        await message.answer(text=f'У вас нет предстоящих дедлайнов')


class DeadlineDone(StatesGroup):
    name = State()


@dispatcher.message_handler(commands=['deadline_done'])
async def deadline_done(message: types.Message):
    await message.answer(text='Введите id выполненной задачи')
    await DeadlineDone.name.set()


@dispatcher.message_handler(state=DeadlineDone.name)
async def deadline_done_name(message: types.Message, state: FSMContext):
    res = db.set_deadline_done(int(message.text), message.from_user.id)
    if res:
        await message.answer(text=f"Задача {message.text} завершена")
    else:
        await message.answer(text=f"У вас нет задачи с id = {message.text}")
    await state.finish()


class DeleteDeadline(StatesGroup):
    name = State()


@dispatcher.message_handler(commands=['delete_deadline'])
async def deadline_delete(message: types.Message):
    await message.answer(text='Введите id задачи')
    await DeleteDeadline.name.set()


@dispatcher.message_handler(state=DeleteDeadline.name)
async def deadline_delete_name(message: types.Message, state: FSMContext):
    if db.delete_deadline(int(message.text), message.from_user.id):
        await message.answer(text=f"Задача {message.text} удалена")
    else:
        await message.answer(text=f"У вас нет задачи с id = {message.text}")
    await state.finish()



class DeleteProject(StatesGroup):
    name = State()


@dispatcher.message_handler(commands=['delete_project'])
async def project_delete(message: types.Message):
    await message.answer(text='Название проекта')
    await DeleteProject.name.set()


@dispatcher.message_handler(state=DeleteProject.name)
async def project_delete_name(message: types.Message, state: FSMContext):
    await message.answer(text=f"Проект {message.text} удален")
    await state.finish()




class DeleteProjectDeadline(StatesGroup):
    project_name = State()
    task_name = State()

@dispatcher.message_handler(commands=['delete_project_deadline'])
async def project_deadline_delete(message: types.Message):
    await message.answer(text='Название проекта')
    await DeleteProjectDeadline.project_name.set()


@dispatcher.message_handler(state=DeleteProjectDeadline.project_name)
async def project_deadline_delete_proj_name(message: types.Message, state: FSMContext):
    await message.answer(text="Название задачи")
    await state.update_data(project_name=message.text)
    await DeleteProjectDeadline.task_name.set()


@dispatcher.message_handler(state=DeleteProjectDeadline.task_name)
async def project_deadline_delete_task_name(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    data = await state.get_data()
    await message.answer(f"Название проекта: {data['project_name']}\n"
                         f"Название удаленной задачи: {data['task_name']}")
    await state.finish()






@dispatcher.message_handler()
async def smth(message: types.Message):
    await message.answer(text='Я такого не понимаю, напишите /help')


if __name__ == '__main__':
    executor.start_polling(dispatcher)
