from datetime import datetime
from gevent import sleep
from models import *
from sqlalchemy import desc
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.query import Query
from typing import Tuple, Optional


def create_year(year: int) -> None:
    months = [Months(month=month, year=year) for month in range(1, 13)]
    db.session.add_all(months)
    db.session.commit()

def generate_sql_table(main_table: Model, 
                  additional_tables: list[Model | Query], 
                  additional_id: list[Tuple[str, str]],
                  year: int,
                  iterator: Optional[range] = None,
                  iterator_column_name: Optional[str] = None
                  ):
    facilities = Facilities.query.all()
    data = []
    for facility in facilities:
        for month in Months.query.filter(Months.year == year).all():
            for add_table, add_id in zip(additional_tables, additional_id):
                if isinstance(add_table, Query):
                    add_table = add_table.all()
                else:
                    add_table = add_table.query.all()
                for add_row in add_table:
                    if iterator is not None:
                        for i in iterator:
                            init_dict = {'month_id': month.id, 'facility_id': facility.id, iterator_column_name: i}
                            init_dict[add_id[0]] = getattr(add_row, add_id[1])
                            data.append(main_table(**init_dict))
                    else:
                        init_dict = {'month_id': month.id, 'facility_id': facility.id}
                        init_dict[add_id[0]] = getattr(add_row, add_id[1])
                        data.append(main_table(**init_dict))
    db.session.add_all(data)
    db.session.commit()


def check_year():
    if Months.query.order_by(desc(Months.year)).first() < datetime.today().year:
        create_year(datetime.today().year)
        check_year()
    else:
        sleep(86400)