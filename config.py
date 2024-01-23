import logging


class Config:
    #tg_token = "6760184762:AAFyc5KNlzv80v3zc4TDOiaPBVRvCbFE_9M"
    tg_token = "6337716034:AAHkUM9PXDMqcGuwlcxf9OHNOdOmdzJQ_mc"
    #categories_db_pass = "..\\DB\\categories.db"
    db_pass = "DB\\main_db.db"
    user_table_name = "users"
    history_table_name = "history_of_marks"
    mass_splitter = ", "
    logging_level = logging.DEBUG
    timeout_for_goods = 12*60*60  # сутки


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    level=Config.logging_level,
    filename='logs.txt ')
