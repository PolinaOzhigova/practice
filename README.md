# Микросервис для сбора данных и генерации графика

## Описание
Данный микросервис собирает данные у пользователей и выдает им необходимый график

# Инструкция по запуску

1 Создайте и активируйте виртуальное окружение (Anaconda или miniconda).

   ```shell
   conda deactivate
   conda create -n turkey_eq python=3.10
   conda activate turkey_eq
```
2 Установите cartopy.

```conda install cartopy```

3 Клонируйте репозиторий и перейдите в папку с микросервисом.

```
git clone https://github.com/PolinaOzhigova/practice/tree/master
cd ~
```

4 Установите и запустите poetry

```
pip install poetry
poetry install
```

5 Запустите микросервис

```uvicorn app.main:api --reload --port 8083```
