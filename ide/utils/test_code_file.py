"""тестовый код"""
import os


def main():
    """Основная функция"""
    with open("file.txt", "w", encoding="utf-8") as file:
        file.write("some data")
    for i in range(4):
        for j in range(i):
            new_dir = os.path.join(f'new_dir{i+j}')
            os.mkdir(new_dir)
            os.chdir(new_dir)
        with open(f'new_file{i}', 'w', encoding='utf-8') as file:
            pass
        os.chdir('/home/prom/PycharmProjects/shp_ide/ide/test_code/')


if __name__ == "__main__":
    main()
