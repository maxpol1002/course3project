from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaVideo
)

from telegram.ext import ContextTypes


async def send_media(report, user_id, msg_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    if report.get_media():
        report_photos, report_videos, report_docs = report.get_media()
        if report_photos:
            if len(report_photos) == 1:
                await context.bot.send_photo(user_id, report_photos[0], caption="Added photo ⬆️",
                                             reply_to_message_id=msg_id)

            else:
                photos_list = []
                for photo_id in report_photos:
                    photos_list.append(InputMediaPhoto(media=photo_id))
                await context.bot.send_media_group(user_id, photos_list, caption="Added photos ⬆️",
                                                   reply_to_message_id=msg_id)

        if report_docs:
            if len(report_docs) == 1:
                await context.bot.send_document(user_id, report_docs[0], caption="Added document ⬆️",
                                                reply_to_message_id=msg_id)

            else:
                docs_list = []
                for doc_id in report_docs:
                    docs_list.append(InputMediaDocument(media=doc_id))
                await context.bot.send_media_group(user_id, docs_list, caption="⬇️ Added documents ⬆️",
                                                   reply_to_message_id=msg_id)

        if report_videos:
            if len(report_videos) == 1:
                await context.bot.send_video(user_id, report_videos[0], caption="Added video ⬆️",
                                             reply_to_message_id=msg_id)

            else:
                videos_list = []
                for vid_id in report_videos:
                    videos_list.append(InputMediaVideo(media=vid_id))
                await context.bot.send_media_group(user_id, videos_list, caption="Added videos ⬆️",
                                                   reply_to_message_id=msg_id)


async def print_daily_reports(update: Update, context: ContextTypes.DEFAULT_TYPE, daily_reports) -> None:
    for report in daily_reports:
        delete_button = [
            [InlineKeyboardButton("❌ Delete", callback_data=f"delete_daily_{report.report_id}")]
        ]
        msg = await update.message.reply_text(report.create_report_text(),
                                              reply_markup=InlineKeyboardMarkup(delete_button))
        await send_media(report, 648380859, msg.id, context)


async def print_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE, tasks) -> None:
    for task in tasks:
        if task.task_status == "completed":
            delete_button = [
                [InlineKeyboardButton("❌ Delete", callback_data=f"delete_task_{task.task_id}")]
            ]
            msg = await update.message.reply_text(task.print_data(), reply_markup=InlineKeyboardMarkup(delete_button))
        else:
            msg = await update.message.reply_text(task.print_data())

        await send_media(task, 648380859, msg.id,  context)


async def print_reports(update: Update, context: ContextTypes.DEFAULT_TYPE, reports) -> None:
    for report in reports:
        if report.report_status == "pending":
            approve_report_button = [
                [InlineKeyboardButton("✅ Approve",
                                      callback_data=f"approve_report_{report.report_id}_{report.task_id}_{report.user_id}"),
                 InlineKeyboardButton("🔄 Dismiss",
                                      callback_data=f"dismiss_report_{report.report_id}_{report.task_id}_{report.user_id}")]
            ]

            msg = await update.message.reply_text(report.create_report_text(),
                                                  reply_markup=InlineKeyboardMarkup(approve_report_button))
        else:
            delete_button = [
                [InlineKeyboardButton("❌ Delete", callback_data=f"delete_report_{report.report_id}")]
            ]
            markup = InlineKeyboardMarkup(delete_button)
            msg = await update.message.reply_text(report.create_report_text(), reply_markup=markup)

        await send_media(report, 648380859, msg.id, context)
