I wrote a Python program named `pi_series.py` to calculate the first 1,000,000 terms of the series

`1 - 1/3 + 1/5 - 1/7 + ...`

and multiply the sum by 4.

Program content:
```python
def calculate_pi_like_series(n_terms: int = 1_000_000) -> float:
    total = 0.0
    sign = 1.0
    for i in range(n_terms):
        denominator = 2 * i + 1
        total += sign / denominator
        sign *= -1.0
    return 4 * total


if __name__ == '__main__':
    result = calculate_pi_like_series()
    print(result)
```

I also ran the script in the sandbox.