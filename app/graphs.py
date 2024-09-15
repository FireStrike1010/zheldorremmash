import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from models import *
from typing import List, Any, Optional
from collections.abc import Sequence
from flask_sqlalchemy.model import Model
from functools import reduce
from datetime import datetime


month_names = {1: 'Январь',
               2: 'Февраль',
               3: 'Март',
               4: 'Апрель',
               5: 'Май',
               6: 'Июнь',
               7: 'Июль',
               8: 'Август',
               9: 'Сентябрь',
               10: 'Октябрь',
               11: 'Ноябрь',
               12: 'Декабрь'}

def chained_getattr(obj: Any,
                    attr_chain: str | Sequence[str],
                    default: Optional[Any] = None) -> Any:
    if isinstance(attr_chain, str):
        attr_chain = attr_chain.split('.')
    return reduce(lambda o, attr: getattr(o, attr, default), attr_chain, obj)

def get_data_frame(data: List[Model],
                   columns: List[Any],
                   columns_name: Optional[List[str]] = None,
                   dtypes: Optional[List[str]] = None) -> pd.DataFrame:
    raw_data = [[chained_getattr(row, attr_chain=attr_chain) for attr_chain in columns] for row in data]
    df = pd.DataFrame(raw_data, columns=columns_name)
    if dtypes is not None:
        df = df.astype(dict(zip(columns_name, dtypes)))
    return df


def plot_TargetIndicator(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = TargetIndicator.query.filter(TargetIndicator.facility_id == facility_id,
                                        TargetIndicator.month_id.in_(months_ids)).all()
    df = get_data_frame(data,
                        columns=['month.month', 'target_plan', 'mandatory_plan', 'fact'],
                        columns_name=['Month', 'Target Plan', 'Mandatory Plan', 'Fact'],
                        dtypes=['category', 'float32', 'float32', 'float32'])
    df = df.groupby(by='Month').agg('sum').reset_index().sort_values(by='Month')
    df['Month'] = df['Month'].replace(month_names)
    df[['Target Plan', 'Mandatory Plan', 'Fact']] = df[['Target Plan', 'Mandatory Plan', 'Fact']].round(2)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df['Fact'], x=df['Month'],
                         text=df['Fact'].astype('object'), textposition='inside', textfont={'color': '#FFFFFF'},
                         marker={'color': '#C0504D'}, name='Факт'))
    fig.add_trace(go.Scatter(y=df['Target Plan'], x=df['Month'],
                             mode='lines+markers+text',
                             text=df['Target Plan'], textposition='top right', textfont={'color': '#9BBB59'},
                             marker={'color': '#9BBB59'},
                             name='План'))
    fig.add_trace(go.Scatter(y=df['Mandatory Plan'], x=df['Month'],
                             mode='lines+markers+text',
                             text=df['Mandatory Plan'], textposition='top left', textfont={'color': '#1C3572'},
                             marker={'color': '#1C3572'}, name='Обязательство'))
    fig.update_traces(texttemplate='%{text:.2f}')
    fig.update_layout(title={'text': 'Достижение целевого показателя по ДК ТОС', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

def plot_TargetIndicator_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = TargetIndicator.query.filter(TargetIndicator.facility_id == facility_id,
                                            TargetIndicator.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = TargetIndicator.query.filter(TargetIndicator.facility_id == facility_id,
                                            TargetIndicator.month_id.in_(month_id)).all()
        title = 'Годовая оценка'
    df = get_data_frame(data,
                        columns=['mandatory_plan', 'fact'],
                        columns_name=['Mandatory Plan', 'Fact'],
                        dtypes=['float32', 'float32'])
    df = df.sum()
    df['Fact'] = 1.0 if df['Mandatory Plan'] == 0.0 else df['Fact']/df['Mandatory Plan']
    df['Gap'] = 1.0 - df['Fact']
    df = df.round(2)
    fig = go.Figure()
    fig.add_trace(go.Pie(values=[df['Fact'], df['Gap']],
                         labels=['Факт', 'Отставание'],
                         marker={'colors': ['#1C3572', '#C0504D']},
                         hole=0.7,
                         textposition='inside',
                         textinfo='percent'))
    fig.update_layout(title={'text': title, 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2, 'xanchor': 'center', 'x': 0.5},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    return fig

def plot_ActionPlanImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = ActionPlanImplementation.query.filter(ActionPlanImplementation.facility_id == facility_id,
                                                 ActionPlanImplementation.month_id.in_(months_ids)).all()
    df = get_data_frame(data,
                        columns=['month.month', 'plan', 'fact'],
                        columns_name=['Month', 'Plan', 'Fact'],
                        dtypes=['category', 'float32', 'float32'])
    df = df.groupby(by='Month').sum().reset_index().sort_values(by='Month')
    df['Fact'] = df['Fact'].cumsum()
    df['Plan'] = df['Plan'].cumsum()
    currunt_month_id = df.loc[df['Month'] == datetime.now().month].index[0]
    df['Month'] = df['Month'].replace(month_names)
    df.loc[df.index > currunt_month_id, 'Fact'] = None
    df[['Plan', 'Fact']] = df[['Plan', 'Fact']].round(2)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df['Fact'], x=df['Month'],
                         text=df['Fact'], textposition='inside', textfont={'color': '#FFFFFF'},
                         marker={'color': '#C0504D'}, name='Факт'))
    fig.add_trace(go.Scatter(y=df['Plan'], x=df['Month'],
                             mode='lines+markers+text',
                             text=df['Plan'], textposition='top left', textfont={'color': '#1C3572'},
                             marker={'color': '#1C3572'}, name='План'))
    fig.update_traces(texttemplate='%{text:.2f}')
    fig.update_layout(title={'text': 'Исполнение плана мероприятий по ДК ТОС', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

def plot_ActionPlanImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = ActionPlanImplementation.query.filter(ActionPlanImplementation.facility_id == facility_id,
                                                     ActionPlanImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = ActionPlanImplementation.query.filter(ActionPlanImplementation.facility_id == facility_id,
                                                     ActionPlanImplementation.month_id.in_(month_id)).all()
        title = 'Годовая оценка'
    df = get_data_frame(data,
                        columns=['month.month', 'plan', 'fact'],
                        columns_name=['Month', 'Plan', 'Fact'],
                        dtypes=['category', 'float32', 'float32'])
    df = df.groupby(by='Month').sum().reset_index().sort_values(by='Month')
    df['Plan'] = df['Plan'].cumsum()
    df['Fact'] = df['Fact'].cumsum()
    df = df[['Plan', 'Fact']]
    df = df.sum()
    df['Fact'] = 1.0 if df['Plan'] == 0.0 else df['Fact']/df['Plan']
    df['Gap'] = 1.0 - df['Fact']
    df = df.round(2)
    fig = go.Figure()
    fig.add_trace(go.Pie(values=[df['Fact'], df['Gap']],
                         labels=['Факт', 'Отставание'],
                         marker={'colors': ['#1C3572', '#C0504D']},
                         hole=0.7,
                         textposition='inside',
                         textinfo='percent'))
    fig.update_layout(title={'text': title, 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2, 'xanchor': 'center', 'x': 0.5},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    return fig