def extract_keys(task_name):
    name = task_name.split("課題")[1]
    split_name = name.split("-")
    numbers = [int(n) for n in split_name if n.isdigit()]
    numbers = numbers[:-1]
    return numbers
