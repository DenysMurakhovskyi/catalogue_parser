import logging
from typing import NoReturn

import pandas as pd
from PySide6.QtCore import QObject, Signal

from application import config

EXCEL_COLUMNS = ['Код_поставщика', 'Наименование', 'Цена', 'Флаг_добавления']



class Synchronizer(QObject):
    finished = Signal()
    message = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('file_logger')

    def sync_tables(self, supplier_data: pd.DataFrame, google_sheet_data: pd.DataFrame) -> pd.DataFrame:
        """
        Make changes in google table data, read and write excel data
        :return: updated dataframe with changes in google data
        """
        self.logger.debug('Synchronization started')
        self.logger.debug(f'Catalogue dataframe shape {supplier_data.shape}')
        self.logger.debug(f'Google dataframe shape {google_sheet_data.shape}')
        self.message.emit('Почато синхронізацію отриманих даних')

        existing_articles = \
            supplier_data.loc[supplier_data['article'].isin(google_sheet_data['Код_поставщика'].values)]

        self._new_articles_to_excel(google_sheet_data, supplier_data)

        df = self._add_data_to_google_table(google_sheet_data, existing_articles)
        self.logger.debug(f'Add data dataframe shape {df.shape}')
        self.finished.emit()

    @classmethod
    def _new_articles_to_excel(cls, google_sheet_data, supplier_data) -> NoReturn:
        """
        Choose data to write into the Excel table
        :param google_sheet_data: dataframe with data from the Google sheet
        :param supplier_data: dataframe with data from the supplier's site
        :return: None
        """
        excel_df = cls._read_excel()
        supplier_data['article'] = supplier_data['article'].astype('int64')
        not_existing_present_articles = \
            supplier_data.loc[~supplier_data['article'].isin(google_sheet_data['Код_поставщика'].values)]
        not_existing_present_articles = \
            not_existing_present_articles.loc[not_existing_present_articles.quantities > 0]
        not_existing_present_articles = \
            not_existing_present_articles.loc[
                ~not_existing_present_articles['article'].isin(excel_df['Код_поставщика'])]
        not_existing_present_articles.drop(columns=['quantities'], inplace=True)
        not_existing_present_articles.rename(columns={'names': 'Наименование',
                                                      'article': 'Код_поставщика',
                                                      'prices': 'Цена'},
                                             inplace=True)
        not_existing_present_articles['Флаг_добавления'] = '-'
        excel_df = pd.concat([excel_df, not_existing_present_articles]).reset_index(drop=True)
        cls._write_excel(excel_df)

    @classmethod
    def _add_data_to_google_table(cls, google_df: pd.DataFrame, supplier_df: pd.DataFrame) -> pd.DataFrame:
        """
        Updates data in the dataframe with data from the google table
        :param google_df: dataframe with data from the google sheet
        :param supplier_df: dataframe with data from the supplier's site
        :return:
        """
        google_df['change_flag'] = False
        for index, row in google_df.iterrows():
            try:
                supplier_data = supplier_df.loc[supplier_df['article'] == row['Код_поставщика']].iloc[0]
            except Exception as ex:
                continue

            if row[config.price_sync_column] != supplier_data['prices']:
                google_df.at[index, config.price_sync_column] = supplier_data['prices']
                google_df.at[index, 'change_flag'] = True

            if (row[config.availability_sync_column] == '+') & (supplier_data['quantities'] <= 0):
                google_df.at[index, config.availability_sync_column] = '-'
                google_df.at[index, 'change_flag'] = True

            if (row[config.availability_sync_column] == '-') & (supplier_data['quantities'] > 0):
                google_df.at[index, config.availability_sync_column] = '+'
                google_df.at[index, 'change_flag'] = True
        return google_df

    @staticmethod
    def _read_excel() -> NoReturn:
        """
        Reads Excel file
        :return: None
        """
        if (path := config.assets_dir / config.excel_file_name).exists():
            return pd.read_excel(path, index_col=0)
        else:
            return pd.DataFrame(columns=EXCEL_COLUMNS)

    @staticmethod
    def _write_excel(df: pd.DataFrame) -> NoReturn:
        """
        Writes excel file
        :param df: data to write
        :return: None
        """
        df.to_excel(config.assets_dir / config.excel_file_name)
