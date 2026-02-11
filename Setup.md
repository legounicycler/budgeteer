# Steps to set up budgeteer

(All steps are run from the From the `budgeteer/` directory)

## 1. Set up python virtual environment
``` bash
python -m venv ./.venv
. ./.venv/Scripts/activate
```

## 2. Install python requirements
``` bash
pip install -r requirements.txt
```

## 3. Install the javascript dependencies
``` bash
cd static
npm install
cd ..
```

## 4. Download the sercret.py file
1. Set `IS_PRODUCTION_MACHINE` to `False`
2. Set `LOCAL_DATABASE_PATH` to point to inside the `budgeteer/` directory
   1. Create a `database.sqlite` file
   2. Right click in VSCode and click "Copy Path"
   3. Paste it into the `secret.py` file
   4. Delete `database.sqlite`
3. Set `LOCAL_UPLOADS_FOLDER` to point to the `budgeteer/uploads/` directory

## 5. Run `create_db.py`
``` bash
python create_db.py
# or
python create_db.py --default-user
```

## 6. Start the app
``` bash
python budgeteer.py
```

## 7. Open the web browser
Go to [localhost:5000](localhost:5000)