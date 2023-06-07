from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, types
from sqlalchemy.sql.schema import ForeignKey
from flask_restful import Resource, Api
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_swagger_ui import get_swaggerui_blueprint # solo para casos de no usar POSTMAN // DEJO INDICADO EN FLECHA # <==||
from flask_cors import CORS
from os import environ
from dotenv import load_dotenv # Utilizando variables de entorno, permite proteger y ocultar variables de configuracion o API KEYS o DATA SENSIBLE. EJEMPLO PARA QUE YA NO SE VEA LA CONEXIÓN A LA BD Y SE CREE UN .ENV EN ARCHIVO APARTE
#gunicorn nos brinda un servidor wsgi para servidores o proyectos de python, básicamente para servidores de produccion
#https://gunicorn.org/
load_dotenv()

SWAGGER_URL = '/api-docs' # <==||
API_URL = '/static/documentacion.json' # <==||

app = Flask(__name__)
CORS(app=app) # DETERMINA QUIEN PUEDE TENER ACCESO A NUESTRO BACKEND // EN ESTE CASO SE HABILITA PARA CUALQUIERA

configuracion_swagger = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={
    'app_name': 'Documentacion de la API' #Titulo de la pagina de la documentacion
})# <==||

# Permite cargar un submodulo dentro de Flask, carga FlaskSwaggerUI
app.register_blueprint(configuracion_swagger) # estamos agregando toda la configuracion del swagger a nuestro proyecto de Flask # <==||

# dialect://nombre:password@host/db
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URI')# es reemplazado => 'postgresql://postgres:root@localhost/empresa' por environ

api = Api(app=app)

conexion = SQLAlchemy(app=app)

class Trabajador(conexion.Model):
    id = Column(type_=types.Integer, autoincrement = True, primary_key= True)
    nombre = Column(type_=types.String(length=100), nullable = False)
    habilitado = Column(type_=types.Boolean, default=True)
    #sirve para indicar lo que vendría a ser el nombre de la tabla pero en la BD
    __tablename__ = 'trabajadores'

class Direccion(conexion.Model):
    id = Column(type_=types.Integer, autoincrement=True, primary_key=True)
    nombre = Column(type_=types.String(length=250), nullable=True)
    numero = Column(type_=types.Integer)
    # llave foranea
    trabajadorId = Column(ForeignKey(column='trabajadores.id'), type_=types.Integer, nullable=False, name = 'trabajador_id')

    __tablename__ = 'direcciones'

@app.before_request
def inicializador():
    print('Yo me ejecuto una sola vez')
    conexion.create_all()

@app.route('/trabajadores', methods =['GET','POST'])
def manejo_trabajadores():
    if request.method == 'GET':
        # retorna una lista de instancia de la clase trabajador
        resultado: list[Trabajador] = conexion.session.query(Trabajador).all()
        print(resultado)
        trabajadores = []

        for trabajador in resultado:
            trabajadores.append({
                'id': trabajador.id,
                'nombre': trabajador.nombre,
                'habilitado': trabajador.habilitado
                })
                       
        return{
            'content': trabajadores
        }
    elif request.method =='POST':
        data = request.get_json()
        # {'nombre': 'juanito','habilitado': True}
        nuevoTrabajador = Trabajador(nombre=data.get('nombre'), habilitado = data.get('habilitado'))
        # Registramos los cambios en la base de datos
        conexion.session.add(nuevoTrabajador)
        #Guardamos los cambios de manera permanente
        conexion.session.commit()
        return{
            'message':' Trabajador creado exitosamente'
        }

@app.route('/direcciones', methods = [ 'POST'])
def gestion_direcciones():
    if request.method=='POST':
        try:
            data = request.get_json()
            # {'nombre': '...', 'numero': 123, 'trabajadorId':1}
            nuevaDireccion = Direccion(**data) # nombre ='...', numero = 123, trabajadorId = 1
            conexion.session.add(nuevaDireccion)
            conexion.session.commit()
            return{
                'message': 'Direccion agregada exitosamente'
            }
        except:
            return{
                'message': 'Error al agregar dirección'
            }, 400
        
@app.route('/direccion/<int:trabajadorId>', methods=['GET'])
def devolver_direcciones(trabajadorId):
    # SELECT * FROM direcciones WHERE trabajador_id = ...;
    resultado: list[Direccion] = conexion.session.query(Direccion).filter_by(trabajadorId=trabajadorId).all()
    print(resultado)
    dto = TrabajadorDTO()
    result = dto.dump(resultado, many=True)
    # direcciones = []
    # for direccion in resultado:
    #     direcciones.append({
    #         'id': direccion.id,
    #         'nombre': direccion.nombre,
    #         'numero': direccion.numero
    #     })
    return{
        'content': result
    }
# Data Transfer Object
class TrabajadorDTO(SQLAlchemyAutoSchema):
    class Meta:
        # permite modificar el atributo model sin la necesidad de modificar la clase como tal
        # model > sirve para indicar en que tabla o modelo se tiene que basar para hacer las validaciones
        model = Trabajador


class TrabajadorController(Resource):
    def get(self):
        trabajadores: list[Trabajador] = conexion.session.query(Trabajador).all()
        dto = TrabajadorDTO()
        # Transforma la información proveniente del ORM a una información legible(diccionario)
        # NOTA: si yo le paso un listado de informacion entonces adicionalmente agrego la propiedad many = True
        resultado = dto.dump(trabajadores, many=True)
        # resultado = []
        # for trabajador in trabajadores:
        #     resultado.append({
        #         'id': trabajador.id,
        #         'nombre': trabajador.nombre,
        #         'habilitado': trabajador.habilitado
        #     })
        return{
            'message': resultado
        }
    def post(self):
        data = request.get_json()
        dto = TrabajadorDTO()
        try:
            # sirve para cargar la informacion y validar si es correcta, si no es correcta entonces emitira un error con las incorreciones
            dataValidada = dto.load(data)
            print(dataValidada)
            nuevoTrabajador = Trabajador(**dataValidada)
            conexion.session.add(nuevoTrabajador)
            conexion.session.commit()
            return{
                'message': 'Trabajador creado exitosamente'
            }
        except Exception as e:
            return {
                'message': 'Error al crear el nuevo trabajador',
                'content': e.args
            }

class TrabajadorUnitarioController(Resource):
    dto = TrabajadorDTO()
    def get(self, id): # id<==========
        trabajador = conexion.session.query(Trabajador).filter_by(id=id).first() # .first para obtener la primera coincidencia
        resultado = self.dto.dump(trabajador)
        return{
            'content': resultado
        }
    def put(self,id):
        trabajador = conexion.session.query(Trabajador).filter_by(id=id).first()
        if trabajador is None:
            return{
                'message': 'Trabajador no existe'
            }
        data = request.get_json()
        data_validada = self.dto.load(data)
        trabajador.nombre = data_validada.get('nombre')
        trabajador.habilitado = data_validada.get('habilitado', trabajador.habilitado) # el metodo get permite mencionar que llave utilizar y si la llave no esta => 'habilitado', utiliza el valor por defecto => trabajador.habilitado

        conexion.session.commit()

        return{
            'message': 'Trabajador actualizado exitosamente'
        }
    
    def delete(self, id):
        trabajador = conexion.session.query(Trabajador).filter_by(id=id).first()
        direcciones = conexion.session.query(Direccion).filter_by(trabajadorId=id).all()
        if trabajador is None:
            return{
                'message': 'Trabajador no existe'
            }
        if len(direcciones) is not 0:
            return{
                'message': 'Trabajador no se puede eliminar, porque tiene direcciones. Elimine primero las direcciones'
            }
        conexion.session.delete(trabajador)
        conexion.session.commit()

        return{
            'message': 'Trabajador eliminado exitosamente'
        }

api.add_resource(TrabajadorController, '/api/trabajadores')
# EL MISMO NOMBRE QUE DECLARE EN MI PARÁMETRO (DONDE MARCA LA FLECHA) DEBO DECLARAR EN MI RUTA
api.add_resource(TrabajadorUnitarioController, '/api/trabajador/<int:id>') # id<========

# app.run(debug=True)