#
d = {11: 'one', 2: 'two', 3: 'three', 4: 'four', '4': 'four_str_key', 
        True: 'Istina', 'dict': {'one': 1, 'two': 2}, 'house': ['дом', 'жилище', 'хижина'], 5.6: 5.6}



lst = [['key1', 'value1'], ['key2', 'value1'], ['key3', 'value3']]

i = 'one=1 two=2 three=3'
lst = [['key1', 'value1'], ['key2', 'value1'], ['key3', 'value3']]
# a = dict(one=1,two=2,three=3)   // NEEDED RESULT

t = [list(x) for x in i.split()]
print(t)

print(i.split())


