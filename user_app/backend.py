import functools


class SqlEngine:

    def __init__(self, conn, model):
        self.conn = conn
        self.model = model

    def insert(self, values: tuple):  # Add async
        return Insert(self.model, values)

    def select(self, values: tuple):  # Add async
        return Select(self.model, values)


class SqlFunc:
    """
    Abstract class of every method
    """

    @staticmethod
    def check_args(model, values: tuple):
        """
        Delete unexpected args from sql expression.

        :param model: model instance
        :param values: tuple of dict of values
        :return: list of expected args, or list of args for insert/update etc
        """
        table_name = model.name
        if all(isinstance(elem, dict) for elem in values):
            identical_params = functools.reduce(lambda x, y: set(x) & set(y), [elem.keys() for elem in values])
            coincidence = list(set(model.columns.keys()) & set(identical_params))
            return table_name, coincidence, [str(tuple(elem[key] for key in coincidence)) for elem in values]
        else:
            coincidence = list(set(model.columns.keys()) & set(values))
            return table_name, coincidence

    def where(self):
        pass

    def group_by(self):
        pass

    def having(self):
        pass

    def order_by(self):
        pass

    async def execute(self):
        pass


class Insert(SqlFunc):

    def __init__(self, model, values):
        self.method = __class__.__class__.__name__
        table_name, coincidence, values = SqlFunc.check_args(model, values)
        self.sql_expression = f'INSERT INTO {table_name} ({", ".join(coincidence)}) VALUES {", ".join(values)}'


class Select(SqlFunc):

    def __init__(self, model, values):
        self.method = __class__.__class__.__name__
        table_name, coincidence = SqlFunc.check_args(model, values)
        self.sql_expression = f'SELECT ({", ".join(coincidence)}) FROM {table_name}'


class Update(SqlFunc):
    pass