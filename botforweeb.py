import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import config
import re_bf
import SQLAclhemy_first
import os


# Configure logging
loop = asyncio.get_event_loop()
logging.basicConfig(level=logging.INFO)
# Initialize bot and dispatcher
bot = Bot(token=os.environ["TOKEN"])
#bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)
"""
https://docs.aiogram.dev/en/latest/examples/finite_state_machine_example.html?highlight=StatesGroup
https://mastergroosha.github.io/telegram-tutorial/docs/lesson_14/
По этим ссылкам научился работать с FSM, конечный автомат состояния.
Именно по ним нужно делать пошаговый диалог.
Я юзал простейший способ хранения инфы о состоянии юзера в RAM. То есть вся инфа теряется при перезапуске!!!
"""


class PageState(StatesGroup):
    wait_for_answer_sub = State()
    wait_for_answer_un_sub = State()
    wait_for_url_sub = State()
    wait_for_url_un_sub = State()
    wait_for_url_change = State()
    wait_for_url_change_new = State()


@dp.message_handler(commands=["subscribe"])
async def subscribe(message: types.Message):
    await message.reply("Напишите /substate если хотите снова получать уведомления или \
/addsub если хотите добавить ресурс для отслеживания!")
    await PageState.wait_for_answer_sub.set()


@dp.message_handler(commands=["substate", "addsub"], state=PageState.wait_for_answer_sub)
async def subscribe(message: types.Message, state: FSMContext):
    SQLAclhemy_first.if_user_in_db(message.from_user.id)
    if message.text == '/addsub':
        await PageState.wait_for_url_sub.set()
        await message.reply('Отправте TitleID ресурса MangaDex!')
    else:
        if not SQLAclhemy_first.if_sub_user(message.from_user.id):
            if SQLAclhemy_first.if_user_have_manga(message.from_user.id):
                await message.reply(SQLAclhemy_first.set_sub_state_on(message.from_user.id))
            else:
                await message.reply("У вас нет ресурсов для отслеживания добавьте их!")
        else:
            await message.reply("Вы уже подписаны!")
        await state.finish()


@dp.message_handler(regexp="\d+", state=PageState.wait_for_url_sub)
async def subscribe(message: types.Message, state: FSMContext):
    if not SQLAclhemy_first.if_url_in_db(message.from_user.id, message.text):
        await message.reply(SQLAclhemy_first.subscribe_user(message.from_user.id, message.text))
    else:
        await message.reply('Вы уже подписаны на эту рассылку!')
    await state.finish()


@dp.message_handler(commands=["delete"])
async def delete_sub(message: types.Message):
    if SQLAclhemy_first.if_user_in_db(message.from_user.id):
        if SQLAclhemy_first.if_user_have_manga(message.from_user.id):
            await message.reply("Укажите TitleID который хотите удалить из подписок!")
            await PageState.wait_for_url_un_sub.set()
        else:
            await message.reply("У вас нет ресурсов для отслеживания добавьте их!")
    else:
        await message.reply("У вас нет ресурсов для отслеживания добавьте их!")


@dp.message_handler(regexp="\d+", state=PageState.wait_for_url_un_sub)
async def del_sub(message: types.Message, state: FSMContext):
    if SQLAclhemy_first.if_url_in_db(message.from_user.id, message.text):
        await message.reply(SQLAclhemy_first.delete_sub(message.from_user.id, message.text))
    else:
        await message.reply("Вы не подписаны на этот ресурс!")
    await state.finish()


@dp.message_handler(commands=["unsubscribe"])
async def un_sub(message: types.Message):
    if SQLAclhemy_first.if_user_in_db(message.from_user.id):
        if SQLAclhemy_first.if_sub_user(message.from_user.id):
            await PageState.wait_for_answer_un_sub.set()
            await message.reply("Вы будете отписаны от всех рассылок! Напишите /yes если \
            согласны или /no чтобы отменить текущее действие")
        else:
            await message.reply("Ваша подписка не активна!")
    else:
        await message.reply("Ваша подписка не активна!")


@dp.message_handler(commands=["yes", "no"], state=PageState.wait_for_answer_un_sub)
async def un_sub_ans(message: types.Message, state: FSMContext):
    if message.text == "/yes":
        await message.reply(SQLAclhemy_first.unsubscribe(message.from_user.id))
    else:
        await message.reply("Текущее действие отменено!")
    await state.finish()


@dp.message_handler(commands=["change"])
async def change(message: types.Message):
    if SQLAclhemy_first.if_user_in_db(message.from_user.id):
        if SQLAclhemy_first.if_sub_user(message.from_user.id):
            await message.reply("Отправте TitleID который хотите изменить!")
            await PageState.wait_for_url_change.set()
        else:
            await message.reply("Ваша подписка не активна!")
        if not SQLAclhemy_first.if_user_have_manga(message.from_user.id):
            await message.reply("Вы не подписаны ни на один ресурс")
    else:
        await message.reply("Ваша подписка не активна!")


@dp.message_handler(regexp="\d+", state=PageState.wait_for_url_change)
async def change_ans(message: types.Message, state: FSMContext):
    if SQLAclhemy_first.if_url_in_db(message.from_user.id, message.text):
        await message.reply("Отправьте TitleID на который хотите подписаться!!!")
        SQLAclhemy_first.delete_sub(message.from_user.id, message.text)
        await PageState.wait_for_url_change_new.set()
    else:
        await message.reply("Вы не подписаны на эту россылку!!!")
        await state.finish()


@dp.message_handler(regexp="\d+", state=PageState.wait_for_url_change_new)
async def change_ans(message: types.Message, state: FSMContext):
    if not SQLAclhemy_first.if_url_in_db(message.from_user.id, message.text):
        await message.reply(SQLAclhemy_first.subscribe_user(message.from_user.id, message.text))
    else:
        await message.answer("Вы уже подписаны на эту мангу!\nНо мы уже отписали вас от предыдущей манги,\
                             вам необходимо повторно подписаться на удаленную мангу!")
    await state.finish()


@dp.message_handler(commands=["check"])
async def check_my_sub(message: types.Message):
    if not SQLAclhemy_first.if_user_in_db(message.from_user.id) or not SQLAclhemy_first.if_user_have_manga(message.from_user.id):
        await message.answer("У вас нет ресурсов для отслеживания или ваща подписка не активна!")
    else:
        answer = "Вы следите за:\n"
        sub_list = SQLAclhemy_first.check(message.from_user.id)
        for index, value in enumerate(sub_list):
            answer += f"{index+1}.{value[0]}\nПоследняя глава: {value[1]}\n"
        await message.answer(answer)


async def tum():
    while True:
        await asyncio.sleep(300)
        subs = SQLAclhemy_first.get_all_subs()
        for user_id in subs:
            sub_dict = SQLAclhemy_first.get_all_url_chapter(user_id)
            #print(sub_dict)
            for title_id, chapter in sub_dict.items():
                try:
                    current_chapter, manga_name = re_bf.check(title_id)
                    #print(title_id, current_chapter, chapter)
                except:
                    break
                if current_chapter > chapter:
                    await bot.send_message(chat_id=user_id, text=f"Вышла новая {current_chapter} глава манги {manga_name}, https://mangadex.org/title/{title_id}")
                    SQLAclhemy_first.set_new_chapter(user_id, current_chapter, title_id)


if __name__ == "__main__":
    SQLAclhemy_first.Control()
    dp.loop.create_task(tum())
    executor.start_polling(dp, skip_updates=True, loop=loop)
