"""
V2 Booking Service -- orchestrates the V2 booking constructor flow.
"""

from datetime import date, datetime, timedelta

from codex_tools.booking import (
    BookingMode,
    ChainFinder,
    MasterAvailability,
    NoAvailabilityError,
    SlotCalculator,
)
from codex_tools.booking.adapters import DjangoAvailabilityAdapter
from codex_tools.booking.scorer import BookingScorer, ScoringWeights
from core.logger import log
from django.db import transaction
from django.utils import timezone

# Models for Adapter
from features.booking.models import (
    Appointment,
    AppointmentGroup,
    AppointmentGroupItem,
    BookingSettings,
    Master,
    MasterDayOff,
)
from features.booking.models.client import Client
from features.main.models.service import Service
from features.system.models.site_settings import SiteSettings


class BookingV2Service:
    """
    Оркестратор V2 бронирования.
    """

    def __init__(self) -> None:
        settings = BookingSettings.load()
        self._step_minutes = settings.default_step_minutes

        # Initialize Adapter with all required models
        self._adapter = DjangoAvailabilityAdapter(
            master_model=Master,
            appointment_model=Appointment,
            service_model=Service,
            day_off_model=MasterDayOff,
            booking_settings_model=BookingSettings,
            site_settings_model=SiteSettings,
            step_minutes=self._step_minutes,
        )
        self._calc = SlotCalculator(self._step_minutes)

        # Initialize Scorer with default weights
        self._scorer = BookingScorer(
            weights=ScoringWeights(same_master_bonus=10.0, min_idle_bonus_per_hour=5.0, early_slot_penalty_per_hour=1.0)
        )

    # ---------------------------------------------------------------------------
    # Получение доступных слотов (для UI)
    # ---------------------------------------------------------------------------

    def get_available_slots(
        self,
        service_ids: list[int],
        target_date: date,
        mode: BookingMode = BookingMode.SINGLE_DAY,
        locked_master_id: int | None = None,
        master_selections: dict[int, str] | None = None,
        exclude_appointment_ids: list[int] | None = None,
    ) -> dict[str, bool]:
        settings = BookingSettings.load()
        min_start = self._get_min_start(settings)

        request = self._adapter.build_engine_request(
            service_ids=service_ids,
            target_date=target_date,
            mode=mode,
            locked_master_id=locked_master_id,
            master_selections=master_selections,
        )

        if not request.service_requests:
            return {}

        master_ids = self._collect_master_ids(request)
        availability = self._adapter.build_masters_availability(
            master_ids, target_date, exclude_appointment_ids=exclude_appointment_ids
        )

        service_0_req = request.service_requests[0]
        finder = ChainFinder(step_minutes=self._step_minutes, min_start=min_start)
        valid_starts: dict[str, bool] = {}

        for master_id in service_0_req.possible_master_ids:
            master_avail = availability.get(master_id)
            if not master_avail:
                continue
            for window_start, window_end in master_avail.free_windows:
                slot_starts = self._calc.find_slots_in_window(
                    window_start=window_start,
                    window_end=window_end,
                    duration_minutes=service_0_req.duration_minutes,
                    min_start=min_start,
                )
                for slot_dt in slot_starts:
                    t = slot_dt.strftime("%H:%M")
                    if t in valid_starts:
                        continue

                    restricted = self._restrict_first_service_availability(
                        availability=availability,
                        request=request,
                        target_date=target_date,
                        selected_start_time=t,
                    )
                    result = finder.find(request, restricted, max_solutions=1)
                    if result.has_solutions:
                        valid_starts[t] = True

        return dict(sorted(valid_starts.items()))

    def create_group(
        self,
        client: Client,
        service_ids: list[int],
        target_date: date,
        selected_start_time: str,
        mode: BookingMode = BookingMode.SINGLE_DAY,
        locked_master_id: int | None = None,
        notes: str = "",
        master_selections: dict[int, str] | None = None,
        source: str = Appointment.SOURCE_WEBSITE,
        initial_status: str = Appointment.STATUS_PENDING,
    ) -> AppointmentGroup:
        """
        Создает группу записей с оптимистичной блокировкой.
        Сначала ищет решение без блокировок, затем блокирует только выбранных мастеров и перепроверяет.
        """
        selected_start_time = self._normalize_time(selected_start_time)
        settings = BookingSettings.load()
        min_start = self._get_min_start(settings)

        # 1. Строим запрос
        request = self._adapter.build_engine_request(
            service_ids=service_ids,
            target_date=target_date,
            mode=mode,
            locked_master_id=locked_master_id,
            master_selections=master_selections,
        )

        if not request.service_requests:
            raise NoAvailabilityError(booking_date=target_date)

        # 2. Оптимистичный поиск (Snapshot Read)
        # Собираем всех возможных мастеров, чтобы найти хоть какое-то решение
        all_potential_master_ids = self._collect_master_ids(request)

        # Получаем доступность без блокировки
        snapshot_availability = self._adapter.build_masters_availability(all_potential_master_ids, target_date)

        # Ограничиваем поиск выбранным временем старта
        snapshot_restricted = self._restrict_first_service_availability(
            availability=snapshot_availability,
            request=request,
            target_date=target_date,
            selected_start_time=selected_start_time,
        )

        finder = ChainFinder(step_minutes=self._step_minutes, min_start=min_start)
        snapshot_result = finder.find(request, snapshot_restricted, max_solutions=50)

        if not snapshot_result.has_solutions:
            raise NoAvailabilityError(
                booking_date=target_date,
                service_ids=[s.service_id for s in request.service_requests],
                message="Выбранное время уже занято (snapshot check).",
            )

        # Выбираем лучшее решение из snapshot-результатов
        ranked_snapshot = self._scorer.score(snapshot_result)
        best_chain = self._pick_chain_by_start_time(ranked_snapshot, selected_start_time)

        if not best_chain:
            raise NoAvailabilityError(booking_date=target_date, message="Слот недоступен (snapshot check).")

        # Определяем конкретных мастеров, которых нужно заблокировать
        target_master_ids = [int(item.master_id) for item in best_chain.items]

        # 3. Атомарная блокировка и финальная проверка (Critical Section)
        with transaction.atomic():
            # Блокируем ТОЛЬКО участников сделки
            self._adapter.lock_masters(target_master_ids)

            # Получаем СВЕЖИЕ данные только по этим мастерам
            fresh_availability = self._adapter.build_masters_availability(target_master_ids, target_date)

            # Снова ограничиваем временем старта
            fresh_restricted = self._restrict_first_service_availability(
                availability=fresh_availability,
                request=request,
                target_date=target_date,
                selected_start_time=selected_start_time,
            )

            # Финальная проверка: сможет ли этот конкретный набор мастеров выполнить заказ?
            # Важно: здесь мы уже не ищем "любого" мастера, мы проверяем конкретных,
            # так как fresh_availability содержит ключи только target_master_ids.
            final_result = finder.find(request, fresh_restricted, max_solutions=1)

            if not final_result.has_solutions:
                # Слот ушел за миллисекунды между snapshot и lock
                # В теории можно было бы уйти на ретрай (попробовать других мастеров),
                # но для простоты и надежности пока просто отказываем.
                raise NoAvailabilityError(
                    booking_date=target_date, message="К сожалению, выбранный слот только что был занят."
                )

            # Берем подтвержденное решение
            final_chain = final_result.best

            # 4. Создание записей
            total_duration = sum(item.duration_minutes for item in final_chain.items)

            group = AppointmentGroup.objects.create(
                client=client,
                booking_date=target_date,
                status=initial_status,
                engine_mode=mode.value,
                total_duration_minutes=total_duration,
                notes=notes,
            )

            services_map = {str(s.id): s for s in Service.objects.filter(id__in=service_ids)}
            masters_map = {str(m.pk): m for m in Master.objects.filter(pk__in=target_master_ids)}

            for order, sol_item in enumerate(final_chain.items):
                service = services_map.get(sol_item.service_id)
                master = masters_map.get(sol_item.master_id)

                appointment = Appointment.objects.create(
                    client=client,
                    master=master,
                    service=service,
                    datetime_start=sol_item.start_time,
                    duration_minutes=sol_item.duration_minutes,
                    status=initial_status,
                    source=source,
                )

                AppointmentGroupItem.objects.create(
                    group=group,
                    appointment=appointment,
                    service=service,
                    order=order,
                )

        return group

    def reschedule_group(
        self,
        group_id: int,
        target_date: date,
        selected_start_time: str,
    ) -> AppointmentGroup:
        """
        Переносит существующую группу на новую дату/время с оптимистичной блокировкой.
        """
        selected_start_time = self._normalize_time(selected_start_time)
        group = AppointmentGroup.objects.get(pk=group_id)
        items = list(group.items.all().order_by("order"))

        service_ids = [item.service_id for item in items]
        appointment_ids = [item.appointment_id for item in items]

        request = self._adapter.build_engine_request(
            service_ids=service_ids,
            target_date=target_date,
            mode=BookingMode.SINGLE_DAY,
        )

        # 1. Optimistic Search
        all_potential_ids = self._collect_master_ids(request)

        snapshot_avail = self._adapter.build_masters_availability(
            all_potential_ids, target_date, exclude_appointment_ids=appointment_ids
        )

        snapshot_restricted = self._restrict_first_service_availability(
            availability=snapshot_avail,
            request=request,
            target_date=target_date,
            selected_start_time=selected_start_time,
        )

        finder = ChainFinder(step_minutes=self._step_minutes, min_start=None)
        snapshot_result = finder.find(request, snapshot_restricted, max_solutions=50)

        if not snapshot_result.has_solutions:
            raise NoAvailabilityError(booking_date=target_date, message="Время недоступно.")

        ranked_snapshot = self._scorer.score(snapshot_result)
        best_chain = self._pick_chain_by_start_time(ranked_snapshot, selected_start_time)

        if not best_chain:
            raise NoAvailabilityError(booking_date=target_date)

        target_master_ids = [int(item.master_id) for item in best_chain.items]

        # 2. Atomic Lock & Update
        with transaction.atomic():
            self._adapter.lock_masters(target_master_ids)

            fresh_avail = self._adapter.build_masters_availability(
                target_master_ids, target_date, exclude_appointment_ids=appointment_ids
            )

            fresh_restricted = self._restrict_first_service_availability(
                availability=fresh_avail,
                request=request,
                target_date=target_date,
                selected_start_time=selected_start_time,
            )

            final_result = finder.find(request, fresh_restricted, max_solutions=1)

            if not final_result.has_solutions:
                raise NoAvailabilityError(booking_date=target_date, message="Слот был занят.")

            final_chain = final_result.best
            masters_map = {str(m.pk): m for m in Master.objects.filter(pk__in=target_master_ids)}

            for i, sol_item in enumerate(final_chain.items):
                appt = items[i].appointment
                master = masters_map.get(sol_item.master_id)

                appt.datetime_start = sol_item.start_time
                appt.master = master
                appt.save(update_fields=["datetime_start", "master", "updated_at"])

            group.booking_date = target_date
            group.save(update_fields=["booking_date", "updated_at"])

        log.info("BookingV2Service: Group #{} rescheduled to {} {}", group_id, target_date, selected_start_time)
        return group

    def reschedule_single(
        self,
        appointment_id: int,
        target_date: date,
        selected_start_time: str,
    ) -> Appointment:
        """
        Переносит ОДНУ запись на новую дату/время через V2 движок с оптимистичной блокировкой.
        """
        selected_start_time = self._normalize_time(selected_start_time)
        appointment = Appointment.objects.get(pk=appointment_id)

        request = self._adapter.build_engine_request(
            service_ids=[appointment.service_id],
            target_date=target_date,
            mode=BookingMode.SINGLE_DAY,
        )

        # 1. Optimistic
        all_potential_ids = self._collect_master_ids(request)

        snapshot_avail = self._adapter.build_masters_availability(
            all_potential_ids, target_date, exclude_appointment_ids=[appointment.id]
        )

        snapshot_restricted = self._restrict_first_service_availability(
            availability=snapshot_avail,
            request=request,
            target_date=target_date,
            selected_start_time=selected_start_time,
        )

        finder = ChainFinder(step_minutes=self._step_minutes, min_start=None)
        snapshot_result = finder.find(request, snapshot_restricted, max_solutions=1)

        if not snapshot_result.has_solutions:
            raise NoAvailabilityError(booking_date=target_date, message="Время недоступно.")

        best_chain = snapshot_result.best
        target_master_ids = [int(item.master_id) for item in best_chain.items]

        # 2. Atomic
        with transaction.atomic():
            self._adapter.lock_masters(target_master_ids)

            fresh_avail = self._adapter.build_masters_availability(
                target_master_ids, target_date, exclude_appointment_ids=[appointment.id]
            )

            fresh_restricted = self._restrict_first_service_availability(
                availability=fresh_avail,
                request=request,
                target_date=target_date,
                selected_start_time=selected_start_time,
            )

            final_result = finder.find(request, fresh_restricted, max_solutions=1)

            if not final_result.has_solutions:
                raise NoAvailabilityError(booking_date=target_date, message="Слот был занят.")

            solution = final_result.best
            masters_map = {str(m.pk): m for m in Master.objects.filter(pk__in=target_master_ids)}
            master = masters_map.get(solution.items[0].master_id)

            appointment.datetime_start = solution.items[0].start_time
            appointment.master = master
            appointment.save(update_fields=["datetime_start", "master", "updated_at"])

        log.info(
            "BookingV2Service: Appointment #{} rescheduled to {} {}", appointment_id, target_date, selected_start_time
        )
        return appointment

    def _get_min_start(self, settings: BookingSettings) -> datetime:
        return timezone.localtime() + timedelta(minutes=settings.default_min_advance_minutes)

    @staticmethod
    def _normalize_time(time_str: str) -> str:
        """
        Гарантирует формат HH:MM (например, '9:00' -> '09:00').
        Выбрасывает ValueError если формат неверный.
        """
        try:
            # Парсим гибко, форматируем жестко
            dt = datetime.strptime(time_str.strip(), "%H:%M")
            return dt.strftime("%H:%M")
        except ValueError as e:
            raise ValueError(f"Неверный формат времени: {time_str}. Ожидается HH:MM.") from e

    @staticmethod
    def _collect_master_ids(request) -> list[int]:
        ids: set[int] = set()
        for svc_req in request.service_requests:
            for mid in svc_req.possible_master_ids:
                ids.add(int(mid))
        return list(ids)

    @staticmethod
    def _pick_chain_by_start_time(result, selected_time: str):
        for solution in result.solutions:
            if solution.items and solution.items[0].start_time.strftime("%H:%M") == selected_time:
                return solution
        return None

    def _restrict_first_service_availability(
        self,
        availability: dict,
        request,
        target_date: date,
        selected_start_time: str,
    ) -> dict:
        if not request.service_requests:
            return availability

        service_0_req = request.service_requests[0]

        # selected_start_time уже нормализован через _normalize_time
        selected_dt = timezone.make_aware(
            datetime.combine(
                target_date,
                datetime.strptime(selected_start_time, "%H:%M").time(),
            )
        )
        slot_end_dt = selected_dt + timedelta(minutes=service_0_req.duration_minutes)

        restricted = dict(availability)

        for master_id_str in service_0_req.possible_master_ids:
            if master_id_str not in restricted:
                continue

            orig = restricted[master_id_str]
            new_windows: list[tuple] = []

            for ws, we in orig.free_windows:
                if ws <= selected_dt and we >= slot_end_dt:
                    new_windows = [(selected_dt, we)]
                    break

            if new_windows:
                restricted[master_id_str] = MasterAvailability(
                    master_id=orig.master_id,
                    free_windows=new_windows,
                    buffer_between_minutes=orig.buffer_between_minutes,
                )
            else:
                del restricted[master_id_str]

        return restricted
