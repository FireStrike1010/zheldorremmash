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

#график по тесту 1 - Достижение целевого показателя по ДК ТОС
#график
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

#круговая диаграмма
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

#Тест 2 - Исполнение плана мероприятий по ДК ТОС
#График
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

#Круговая диаграмма
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

#Тест 3 - Уровень внедрения инструмента 5С - неуверен из-за цехов
#График
def plot_LevelImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = LevelImplementation.query.filter(LevelImplementation.facility_id == facility_id,
                                                 LevelImplementation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Уровень внедрения инструмента 5С', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_LevelImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = LevelImplementation.query.filter(LevelImplementation.facility_id == facility_id,
                                                     LevelImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = LevelImplementation.query.filter(LevelImplementation.facility_id == facility_id,
                                                     LevelImplementation.month_id.in_(month_id)).all()
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

#Тест 4 - Внедрение TPM на заводе
#График
def plot_TMPImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = TMPImplementation.query.filter(TMPImplementation.facility_id == facility_id,
                                                 TMPImplementation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Внедрение TPM на заводе', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_TMPImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = TMPImplementation.query.filter(TMPImplementation.facility_id == facility_id,
                                                     TMPImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = TMPImplementation.query.filter(TMPImplementation.facility_id == facility_id,
                                                     TMPImplementation.month_id.in_(month_id)).all()
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

#Тест 5 - Внедрение SMED на заводе
#График
def plot_SMEDImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = SMEDImplementation.query.filter(SMEDImplementation.facility_id == facility_id,
                                                 SMEDImplementation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Внедрение SMED на заводе', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_SMEDImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = SMEDImplementation.query.filter(SMEDImplementation.facility_id == facility_id,
                                                     SMEDImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = SMEDImplementation.query.filter(SMEDImplementation.facility_id == facility_id,
                                                     SMEDImplementation.month_id.in_(month_id)).all()
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

#Тест 6 - Внедрение СОКов на заводе
#График
def plot_SOKImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = SOKImplementation.query.filter(SOKImplementation.facility_id == facility_id,
                                                 SOKImplementation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Внедрение СОКов на заводе', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_SOKImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = SOKImplementation.query.filter(SOKImplementation.facility_id == facility_id,
                                                     SOKImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = SOKImplementation.query.filter(SOKImplementation.facility_id == facility_id,
                                                     SOKImplementation.month_id.in_(month_id)).all()
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

#Тест 7 - Проведение обучения
#График
def plot_ConductingTraining(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = ConductingTraining.query.filter(ConductingTraining.facility_id == facility_id,
                                                 ConductingTraining.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Проведение обучения', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_ConductingTraining_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = ConductingTraining.query.filter(ConductingTraining.facility_id == facility_id,
                                                     ConductingTraining.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = ConductingTraining.query.filter(ConductingTraining.facility_id == facility_id,
                                                     ConductingTraining.month_id.in_(month_id)).all()
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

#Тест 8 - кайдзен деятельность(ППУ) шт. - неуверен из-за цехов
#График
def plot_KaizenActivities(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = KaizenActivities.query.filter(KaizenActivities.facility_id == facility_id,
                                                 KaizenActivities.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Кайдзен деятельность (ППУ) шт.', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_KaizenActivities_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = KaizenActivities.query.filter(KaizenActivities.facility_id == facility_id,
                                                     KaizenActivities.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = KaizenActivities.query.filter(KaizenActivities.facility_id == facility_id,
                                                     KaizenActivities.month_id.in_(month_id)).all()
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
#Тест 9 - Адаптация регламентов
#График
def plot_RegulationsAdaptation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = RegulationsAdaptation.query.filter(RegulationsAdaptation.facility_id == facility_id,
                                                 RegulationsAdaptation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Адаптация регламентов', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_RegulationsAdaptation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = RegulationsAdaptation.query.filter(RegulationsAdaptation.facility_id == facility_id,
                                                     RegulationsAdaptation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = RegulationsAdaptation.query.filter(RegulationsAdaptation.facility_id == facility_id,
                                                     RegulationsAdaptation.month_id.in_(month_id)).all()
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

#Тест 10 - Составление КПСЦ - неуверен из-за цехов
#График
def plot_KPSCCompilation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = KPSCCompilation.query.filter(KPSCCompilation.facility_id == facility_id,
                                                 KPSCCompilation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Составление КПСЦ', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_KPSCCompilation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = KPSCCompilation.query.filter(KPSCCompilation.facility_id == facility_id,
                                                     KPSCCompilation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = KPSCCompilation.query.filter(KPSCCompilation.facility_id == facility_id,
                                                     KPSCCompilation.month_id.in_(month_id)).all()
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

#Тест 11 - Внедрение СВМ
#График
def plot_SVMImplementation(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = SVMImplementation.query.filter(SVMImplementation.facility_id == facility_id,
                                                 SVMImplementation.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Внедрение СВМ', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_SVMImplementation_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = SVMImplementation.query.filter(SVMImplementation.facility_id == facility_id,
                                                     SVMImplementation.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = SVMImplementation.query.filter(SVMImplementation.facility_id == facility_id,
                                                     SVMImplementation.month_id.in_(month_id)).all()
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

#Тест 12 - Обмен опытом
#График
def plot_ExperienceExchange(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = ExperienceExchange.query.filter(ExperienceExchange.facility_id == facility_id,
                                                 ExperienceExchange.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'Обмен Опытом', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_ExperienceExchange_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = ExperienceExchange.query.filter(ExperienceExchange.facility_id == facility_id,
                                                     ExperienceExchange.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = ExperienceExchange.query.filter(ExperienceExchange.facility_id == facility_id,
                                                     ExperienceExchange.month_id.in_(month_id)).all()
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

#Тест 13 - ПС3, млн руб.
#График
def plot_PSZ(facility_id: int, months_ids: List[int]) -> go.Figure:
    data = PSZ.query.filter(PSZ.facility_id == facility_id,
                                                 PSZ.month_id.in_(months_ids)).all()
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
    fig.update_layout(title={'text': 'ПСЗ, млн руб.', 'font': {'color':'#000000'}, 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
                      legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 0.8, 'xanchor': 'center', 'x': 0.5, 'font': {'color': '#000000'}},
                      margin={'t': 10, 'b': 0, 'l': 10, 'r': 10},
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)')
    fig.update_xaxes(showgrid=False, ticks='inside', zeroline=False, color='#000000')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#000000')
    return fig

#Круговая диаграмма
def plot_PSZ_pie(facility_id: int, month_id: Sequence[int] | int) -> go.Figure:
    if isinstance(month_id, int):
        data = PSZ.query.filter(PSZ.facility_id == facility_id,
                                                     PSZ.month_id == month_id).all()
        title = 'Текущий месяц'
    else:
        data = PSZ.query.filter(PSZ.facility_id == facility_id,
                                                     PSZ.month_id.in_(month_id)).all()
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
