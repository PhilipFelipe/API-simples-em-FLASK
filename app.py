from itertools import count
from lib2to3.pgen2.token import OP
from typing import Optional, List
from flask import Flask, request, jsonify
from flask_pydantic_spec import FlaskPydanticSpec, Response, Request
from pydantic import BaseModel, Field
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

server = Flask(__name__)
spec = FlaskPydanticSpec('flask', title='Live de Python')
spec.register(server)
database = TinyDB(storage=MemoryStorage)
c = count()


class QueryPerson(BaseModel):
    id: Optional[int]
    name: Optional[str]
    age: Optional[int]


class Person(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: next(c))
    name: str
    age: int


class People(BaseModel):
    people: List[Person]
    count: int


@server.get('/people')  # Rota, Endpoint, Recurso ...
@spec.validate(
    query=QueryPerson,
    resp=Response(HTTP_200=People)
)
def get_people():
    """ Retorna todas as Pessoas da base de dados. """
    query = request.context.query.dict(exclude_none=True)
    all_people = database.search(
        Query().fragment(query)
    )
    return jsonify(
        People(
            people=all_people,
            count=len(all_people)
        ).dict()
    )


@server.get('/people/<int:id>')  # Rota, Endpoint, Recurso ...
@spec.validate(resp=Response(HTTP_200=Person))
def get_person(id):
    """ Retorna uma Pessoa da base de dados. """
    try:
        person = database.search(Query().id == id)[0]
    except IndexError:
        return {'message': 'Person not found'}, 404
    return jsonify(person)


@server.post('/people')
@spec.validate(body=Request(Person), resp=Response(HTTP_200=Person))
def insert_person():
    """ Insere uma pessoa no banco de dados """
    body = request.context.body.dict()
    database.insert(body)
    return body


@server.put('/people/<int:id>')
@spec.validate(
    body=Request(Person), resp=Response(HTTP_201=Person)
)
def change_person(id):
    """ Altera uma Pessoa do banco de dados. """
    Person = Query()
    body = request.context.body.dict()
    database.update(body, Person.id == id)
    return jsonify(body)


@server.delete('/people/<int:id>')
@spec.validate(resp=Response(HTTP_204=Person)
               )
def delete_person(id):
    """ Remove uma Pessoa do banco de dados. """
    database.remove(Query().id == id)
    return jsonify({})


server.run()
