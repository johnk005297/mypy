def test(a, b, c, units="сантиметры", print_error=True):
    if a + b <= c or a + c <= b or b + c <= a:
        if print_error:
            return "Проверьте введенные стороны треугольника!"
        return

    p = (a + b + c) / 2
    s = (p * (p - a) * (p - b) * (p - c)) ** 0.5  
    return "{} {}".format(round(s,2), units)

abc = [6, 4, 5]
params = dict(units="см.",print_error=True)

print(test(*abc, **params))
