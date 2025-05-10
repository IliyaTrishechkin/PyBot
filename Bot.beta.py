import logging
from telegram import* # Update
from telegram.ext import* # ApplicationBuilder, ContextTypes, CommandHandler
import json

add_json = "C:/Dataj/question.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def read(filename):
    with open(filename, 'r', encoding = 'utf-8') as file:
        return json.load(file)



def write(Data, filename):
    Data = json.dumps(Data)
    Data = json.loads(str(Data))
    with open(filename, "w", encoding = 'utf-8') as file:
       json.dump(Data, file, ensure_ascii=False, indent=4)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привіт, я тест-бот.\n Введи /question \n /answer \n або просто задай питання")



async def com_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Задавай питання")


async def Answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        Data = read(add_json)
        Text = ' '.join(context.args)
        for i in range(len(Text)):
            if Text[i] == '?':
                cut = i+1
        data = [Text[:cut], Text[cut+1:]]
        for i in range (len(Data["Questions"])):
            if Data["Questions"][i][0] == data[0]:
                await context.bot.send_message(chat_id=update.effective_chat.id, text = "Таке питання вже є.")
                break
        else:
            Data["Questions"].append(data)
            write(Data, add_json)
            await context.bot.send_message(chat_id=update.effective_chat.id, text = "Питання прийнято")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Після команди введіть питанння після відповідь.")



async def txt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    data = read(add_json)
    for i in range(len(data["Questions"])):
        if data["Questions"][i][0] == question:
            answer = data["Questions"][i][1]
            break
    else:
        answer = "Це складне питання. Звернітся через годину."
    await context.bot.send_message(chat_id=update.effective_chat.id, text = answer)




if __name__ == '__main__':
    application = ApplicationBuilder().token('7311053326:AAES8JRhk--Nz3fA_LcMjeMvMG5Pr5FfDys').build()
    
    answer = CommandHandler('answer', Answer)
    txt_question_handler = MessageHandler(filters.TEXT, txt_question)
    

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('question', com_question))
    application.add_handler(answer)
    application.add_handler(txt_question_handler)
    
    
    application.run_polling()