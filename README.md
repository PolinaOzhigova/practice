## Микросервис для сбора данных и генерации графика

# Описание
Данный микросервис собирает данные у пользователей и выдает им необходимый график

## Инструкция по запуску

# Создайте и активируйте виртуальное окружение (Anaconda или miniconda).

   ```shell
   conda deactivate
   conda create -n turkey_eq python=3.10
   conda activate turkey_eq
```
# Установите cartopy.

`conda install cartopy`

# Клонируйте репозиторий и перейдите в папку с микросервисом.

```
git clone https://github.com/PolinaOzhigova/practice/tree/master
cd ~
```

# Установите и запустите poetry

```
pip install poetry
poetry install
```

# Запустите микросервис

`uvicorn app.main:api --reload --port 8083`
