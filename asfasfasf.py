
query = dict(
    lol='1',
    asfasf='2',
    aasfsfasf='3',
    asfa12412sf='4',
)

expr = [f'{param} = ${i}' for param, i in zip(query.keys(), range(1, len(query) + 1))]

print(', '.join(expr))