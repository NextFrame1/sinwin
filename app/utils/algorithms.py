

def Luhn(card):
    # Здесь хранится контрольная сумма
    checksum = 0
    # Номер карты переводится из строки в массив. Это нужно для дальнейшей итерации по каждой цифре
    cardnumbers = list(map(int, card))
    # Итерации по каждой цифре
    for count, num in enumerate(cardnumbers):
        # Т.к. счёт идёт с нуля, то если index чётный, значит число стоит на нечётной позиции
        if count % 2 == 0:
            buffer = num * 2
            # Если удвоенное число больше 9, то из него вычитается 9 и прибавляется к контрольной сумме
            if buffer > 9:
                buffer -= 9
            # Если нет, то сразу прибавляется к контрольной сумме
            checksum += buffer
        # Если число стоит на чётной позиции, то оно прибавляется к контрольной сумме
        else:
            checksum += num
    # Если контрольная сумма делится без остатка на 10, то номер карты правильный

    if checksum % 10 == 0:
        return True
    else:
        return False


def is_valid_card(card_number: str) -> bool:
    if len(card_number) == 16 and card_number.isdigit():
        return Luhn(card_number)
    else:
        return None
