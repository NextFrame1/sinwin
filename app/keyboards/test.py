
from typing import List, Dict

# Определение достижений
ACHIEVEMENTS = {
    "users": [100, 250, 500, 750, 1000, 2500, 5000, 10000, 15000, 20000, 25000, 30000, 40000, 50000, 75000, 100000, 150000, 200000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 5000000],
    "deposits": [10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12500000, 15000000, 20000000, 25000000, 50000000, 100000000, 150000000, 200000000, 250000000, 500000000, 750000000, 1000000000, 1500000000, 2000000000, 2500000000, 5000000000],
    "income": [5000, 10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12500000, 15000000, 20000000, 25000000, 50000000, 100000000, 150000000, 200000000, 250000000, 500000000, 750000000, 1000000000, 1500000000, 2000000000, 2500000000, 5000000000],
    "first_deposits": [25, 50, 75, 100, 150, 200, 250, 500, 750, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12500000, 15000000, 20000000, 25000000, 50000000, 100000000, 150000000, 200000000, 250000000, 500000000, 750000000, 1000000000, 1500000000, 2000000000, 2500000000, 5000000000],
    "referrals": [1, 2, 3, 5, 7, 10, 15, 20, 25, 35, 50, 75, 100, 150, 200, 250, 500, 750, 1000, 1500, 2000, 2500, 5000, 10000, 25000],
    "api": [1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12500000, 15000000, 20000000, 25000000, 50000000, 100000000, 150000000, 200000000, 250000000, 500000000, 750000000, 1000000000, 1500000000, 2000000000, 2500000000, 5000000000],
    "signals": [100, 250, 500, 750, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12500000, 15000000, 20000000, 25000000, 50000000, 100000000, 150000000, 200000000, 250000000, 500000000, 750000000, 1000000000, 1500000000, 2000000000, 2500000000, 5000000000]
}

def check_achievements(stats: Dict) -> List[str]:
    achievements = []
    
    # Проверка достижений по пользователям
    users_count = stats["users_today"] + stats["users_yesterday"] + stats["users_lastweek"] + stats["users_month"]
    for threshold in ACHIEVEMENTS["users"]:
        if users_count >= threshold:
            achievements.append(f"Пользователей по Вашим ссылкам: {threshold}")
        else:
            break
    
    # Проверка достижений по депозитам
    deposits = stats["today"]["dep"] + stats["yesterday"]["dep"] + stats["last_week"]["dep"] + stats["last_month"]["dep"]
    total_deposits = sum(dep["amount"] for dep in deposits)
    for threshold in ACHIEVEMENTS["deposits"]:
        if total_deposits >= threshold:
            achievements.append(f"Депозиты: {threshold} рублей")
        else:
            break
    
    # Проверка достижений по доходу
    income = stats["today"]["income"] + stats["yesterday"]["income"] + stats["last_week"]["income"] + stats["last_month"]["income"]
    total_income = sum(inc["x"] for inc in income)
    for threshold in ACHIEVEMENTS["income"]:
        if total_income >= threshold:
            achievements.append(f"Доход: {threshold} рублей")
        else:
            break
    
    # Проверка достижений по первым депозитам
    first_deposits = stats["today"]["firstdep"] + stats["yesterday"]["firstdep"] + stats["last_week"]["firstdep"] + stats["last_month"]["firstdep"]
    total_first_deposits = len(first_deposits)
    for threshold in ACHIEVEMENTS["first_deposits"]:
        if total_first_deposits >= threshold:
            achievements.append(f"Первые депозиты: {threshold}")
        else:
            break
    
    # Проверка достижений по рефералам
    referrals_count = stats.get("referrals_count", 0)
    for threshold in ACHIEVEMENTS["referrals"]:
        if referrals_count >= threshold:
            achievements.append(f"Количество рефералов: {threshold}")
        else:
            break
    
    # Проверка достижений по API
    api_count = stats.get("api_count", 0)
    for threshold in ACHIEVEMENTS["api"]:
        if api_count >= threshold:
            achievements.append(f"API: {threshold}")
        else:
            break
    
    # Проверка достижений по сгенерированным сигналам
    signals_count = sum(stats["signals"].values())
    for threshold in ACHIEVEMENTS["signals"]:
        if signals_count >= threshold:
            achievements.append(f"Сгенерировано сигналов: {threshold}")
        else:
            break
    
    return achievements

# Обновление функции profile_callback
@default_router.callback_query(F.data == "profile", only_confirmed)
async def profile_callback(call: CallbackQuery):
    # ... (существующий код)

    # Получение статистики пользователя
    stats = await APIRequest.post("/stats/get", {"partner_hash": partner_hash})
    
    # Проверка достижений
    achievements = check_achievements(stats)
    
    messages.extend([
        "\n🏆 Достижения:",
        *[f"- {achievement}" for achievement in achievements]
    ])

    await call.message.edit_text(
        "\n".join(messages),
        parse_mode=ParseMode.HTML,
        reply_markup=inline.create_profile_markup(),
    )
