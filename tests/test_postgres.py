import datetime

from file_manager.data.base_model import BaseModel
from file_manager.data.engines.postgres import PsycoPGEngine
from file_manager.data.field import Field
from file_manager.data.query import Query


class TestModel(BaseModel):
    NAME = 'test'
    name = Field(str)
    number = Field(int)
    float = Field(float)
    date = Field(datetime.date)
    time = Field(datetime.datetime)


PsycoPGEngine.setup_model(TestModel)

example = TestModel()
example.name = 'Craig'
example.number = 10
example.float = 12.5
example.date = datetime.date.today()
example.time = datetime.datetime.today()

PsycoPGEngine.create(example)
example.name = 'Not Craig'
example.float = 1.2
PsycoPGEngine.update(example)
PsycoPGEngine.delete(example)

qb = Query(t_name='test')
result = PsycoPGEngine.select(qb)
for item in result:
    PsycoPGEngine.delete(item)
