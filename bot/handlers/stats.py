from datetime import datetime, timedelta
from io import BytesIO

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

from bot.keyboards.inline import get_stats_period_keyboard, get_stats_format_keyboard
from bot.states.onboarding import StatsStates
from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService
from services.statistics_service import StatisticsService
from services.user_service import UserService
from utils.exporters import CSVExporter, JSONExporter
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="stats")


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle /stats command - show statistics options.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user:
        return

    async for session in get_session():
        try:
            stats_service = StatisticsService(session)
            user_service = UserService(session)

            db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not db_user:
                await message.answer(loc.get("errors.generic", lang))
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Check if user has any data
            has_data = await stats_service.has_any_data(db_user)

            if not has_data:
                no_data_msg = loc.get("commands.stats.no_data", lang)
                await message.answer(no_data_msg)
                logger.info("stats_no_data", telegram_id=message.from_user.id)
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Show period selection
            title = loc.get("commands.stats.title", lang)
            select_period = loc.get("commands.stats.select_period", lang)

            await message.answer(
                f"{title}\n\n{select_period}",
                reply_markup=get_stats_period_keyboard(loc, lang),
            )

            await state.set_state(StatsStates.waiting_for_period)

            logger.info("stats_command", telegram_id=message.from_user.id)

        except Exception as e:
            logger.error("stats_command_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break


@router.callback_query(StatsStates.waiting_for_period, F.data.startswith("stats_period_"))
async def handle_period_selection(
    callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle period selection for statistics.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.data or not callback.from_user:
        return

    period = callback.data.split("_")[-1]  # week, month, all, custom

    if period == "custom":
        # Show calendar for start date selection
        date_from_msg = loc.get("commands.stats.custom_date_from", lang)
        calendar = SimpleCalendar(locale=get_user_locale(lang))
        await callback.message.edit_text(
            date_from_msg,
            reply_markup=await calendar.start_calendar()
        )
        await state.set_state(StatsStates.waiting_for_custom_date_from)
        await callback.answer()
        return

    # Calculate date range
    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=7)
        end_date = now
        date_range = loc.get("commands.stats.period_week", lang)
    elif period == "month":
        start_date = now - timedelta(days=30)
        end_date = now
        date_range = loc.get("commands.stats.period_month", lang)
    else:  # all
        start_date = None
        end_date = None
        date_range = loc.get("commands.stats.period_all", lang)

    # Save to state
    await state.update_data(start_date=start_date, end_date=end_date, date_range=date_range)

    # Show format selection
    select_format = loc.get("commands.stats.select_format", lang)
    await callback.message.edit_text(select_format, reply_markup=get_stats_format_keyboard(loc, lang))
    await state.set_state(StatsStates.waiting_for_format)
    await callback.answer()


@router.callback_query(StatsStates.waiting_for_custom_date_from, SimpleCalendarCallback.filter())
async def handle_start_date_selection(
    callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle start date selection from calendar.

    Args:
        callback: Callback query
        callback_data: Calendar callback data
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    calendar = SimpleCalendar(locale=get_user_locale(lang))
    selected, date = await calendar.process_selection(callback, callback_data)

    if selected:
        # Save start date and show calendar for end date
        await state.update_data(start_date=date)
        date_to_msg = loc.get("commands.stats.custom_date_to", lang)
        await callback.message.edit_text(
            date_to_msg,
            reply_markup=await calendar.start_calendar(year=date.year, month=date.month)
        )
        await state.set_state(StatsStates.waiting_for_custom_date_to)


@router.callback_query(StatsStates.waiting_for_custom_date_to, SimpleCalendarCallback.filter())
async def handle_end_date_selection(
    callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle end date selection from calendar.

    Args:
        callback: Callback query
        callback_data: Calendar callback data
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    calendar = SimpleCalendar(locale=get_user_locale(lang))
    selected, date = await calendar.process_selection(callback, callback_data)

    if selected:
        data = await state.get_data()
        start_date = data.get("start_date")

        # Validate date range
        if start_date and date < start_date:
            error_msg = loc.get("commands.stats.invalid_date", lang)
            await callback.answer(error_msg, show_alert=True)
            return

        # Save dates and show format selection
        end_date = date.replace(hour=23, minute=59, second=59)
        start_date = start_date.replace(hour=0, minute=0, second=0)
        date_range = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}"

        await state.update_data(start_date=start_date, end_date=end_date, date_range=date_range)

        select_format = loc.get("commands.stats.select_format", lang)
        await callback.message.edit_text(select_format, reply_markup=get_stats_format_keyboard(loc, lang))
        await state.set_state(StatsStates.waiting_for_format)


@router.callback_query(StatsStates.waiting_for_format, F.data.startswith("stats_format_"))
async def handle_format_selection(
    callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle export format selection.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.data or not callback.from_user:
        return

    format_type = callback.data.split("_")[-1]  # csv or json

    # Get date range from state
    data = await state.get_data()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    date_range = data.get("date_range", "")

    async for session in get_session():
        try:
            stats_service = StatisticsService(session)
            user_service = UserService(session)

            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not db_user:
                await callback.answer(loc.get("errors.generic", lang), show_alert=True)
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Get statistics
            stats = await stats_service.get_statistics(db_user, start_date, end_date)

            if stats["total_sessions"] == 0:
                no_data_msg = loc.get("commands.stats.no_data", lang)
                await callback.message.edit_text(no_data_msg)
                await state.clear()
                await callback.answer()
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Prepare export data
            export_data = await stats_service.prepare_export_data(db_user, start_date, end_date)

            # Generate file
            if format_type == "csv":
                file_bytes = CSVExporter.export_to_bytes(export_data)
                filename = f"sleep_stats_{callback.from_user.id}.csv"
            else:  # json
                file_bytes = JSONExporter.export_to_bytes(export_data)
                filename = f"sleep_stats_{callback.from_user.id}.json"

            # Send file
            file = BufferedInputFile(file_bytes, filename=filename)

            exported_msg = loc.get(
                "commands.stats.exported",
                lang,
                total_sessions=stats["total_sessions"],
                avg_duration=stats["avg_duration"],
                avg_quality=stats["avg_quality"] if stats["avg_quality"] > 0 else "N/A",
            )

            await callback.message.edit_text(exported_msg)
            await callback.message.answer_document(file)

            await state.clear()
            await callback.answer()

            logger.info(
                "stats_exported",
                telegram_id=callback.from_user.id,
                format=format_type,
                sessions=stats["total_sessions"],
            )

        except Exception as e:
            logger.error("stats_export_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)
            await state.clear()

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break


@router.callback_query(F.data == "stats_back")
async def handle_stats_back(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle back button in stats.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    # Go back to period selection
    select_period = loc.get("commands.stats.select_period", lang)
    await callback.message.edit_text(select_period, reply_markup=get_stats_period_keyboard(loc, lang))
    await state.set_state(StatsStates.waiting_for_period)
    await callback.answer()
