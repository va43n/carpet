for i in range(10):
    with open(f'calibration_info.json', 'r') as f:
        print(f'{i} in with')
        if i < 5:
            continue
        print(f'{i} still in with')
    print(f'{i} out of with')
