t = ["– Скажи-ка, дядя, ведь не даром",
    "Я Python выучил с каналом",
    "Балакирев что раздавал?",
    "Ведь были ж заданья боевые,",
    "Да, говорят, еще какие!",
    "Недаром помнит вся Россия",
    "Как мы рубили их тогда!"
    ]

a = [    [y for y in x.split() if len(y) > 3] for x in t
        ]

b = [ [x for x in x.split() if len(x) > 3] for x in t ]


lst = [x**2 for x in [x for x in range(1,6)] ]
print(lst)


