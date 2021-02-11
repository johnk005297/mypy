pill = int(input(("Сколько аскорбинок хотите купить? ")))
has_discount = input("Есть ли у Вас социальная карта? ").upper() in ("YES","Y","1","ДА")

price = 15.35
total_price = price * pill
final_price = total_price

if 0 < pill <= 5:
  print("Продажа по обычной цене")
elif pill < 10:
  final_price *= 0.95
  print("Продажа со скидкой 5%")
else:
  free_count = pill // 10
  final_price -= free_count * price
  print("Каждая 10-ая бесплатно!")

# If has discount - 10% bonus
if has_discount:
  final_price = int(final_price * 0.9)


print("# Соц. карта:", "Да" if has_discount else "Нет")
print("# Скидка: {}", )
print("# Итоговая цена: {}", final_price)

    
#   git commit <file_name> -m "<Message text>"