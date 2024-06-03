import logging

from telegram import Update

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from handlers.callback_handler import callback_data_handler

from handlers.command_handlers import (
    start,
    readme
)

from handlers.message_handlers import (
    task_data_handler,
    message_handler,
    daily_report_handler,
    files_handler,
    report_text_handler,
    dismiss_text_handler,
    send_task,
    send_report,
    send_daily_report
)

from config import (
    TOKEN,
    TASK_DATA,
    REPORT_DATA,
    REPORT_FILES,
    DAILY_REPORT,
    DAILY_REPORT_FILES,
    TASK_FILES,
    DISMISS_REP
)


logging.basicConfig(
    filename='logs/bot.logs',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


if __name__ == '__main__':
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_data_handler),
            MessageHandler(filters.Regex(r'🗓\s*Send\s*daily\s*report'), message_handler)
        ],
        states={
            TASK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_data_handler)],
            TASK_FILES: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, files_handler),
                         MessageHandler(filters.Regex(r'Send\s+task'), send_task)],
            REPORT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_text_handler)],
            REPORT_FILES: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, files_handler),
                           MessageHandler(filters.Regex(r'👌\s*Done'), send_report)],
            DAILY_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, daily_report_handler)],
            DAILY_REPORT_FILES: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, files_handler),
                                 MessageHandler(filters.Regex(r'📩\s*Send\s*daily\s*report'), send_daily_report)],
            DISMISS_REP: [MessageHandler(filters.TEXT & ~filters.COMMAND, dismiss_text_handler)]
        },
        fallbacks=[]
    )
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", readme))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(callback_data_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
