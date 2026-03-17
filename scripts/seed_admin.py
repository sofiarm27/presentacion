import sys
import os

# Añadir el directorio 'backend' al path para poder importar 'app'
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.auth import Usuario, Rol # Modificado para usar los modelos separados
from app.core.security import get_password_hash

# Necesario para crear tablas si no existen
from app.models.auth import Base
Base.metadata.create_all(bind=engine)

def seed_admin():
    db = SessionLocal()
    try:
        # 1. Asegurar que los roles básicos existan
        roles_basicos = ["Administrador", "Abogado"]
        roles_db = {}
        
        for rol_nombre in roles_basicos:
            rol = db.query(Rol).filter(Rol.nombre.ilike(rol_nombre)).first()
            if not rol:
                rol = Rol(nombre=rol_nombre)
                db.add(rol)
                db.commit()
                db.refresh(rol)
                print(f"Rol '{rol_nombre}' creado.")
            roles_db[rol_nombre] = rol
            
        admin_role = roles_db["Administrador"]

        # 2. Verificar si el usuario ya existe
        admin_email = "admin@lexcontract.com"
        admin_user = db.query(Usuario).filter(Usuario.correo == admin_email).first()
        
        if not admin_user:
            admin_user = Usuario(
                nombre="Admin",
                apellido="Sistema",
                cedula="123456789",
                celular="3000000000",
                correo=admin_email,
                password=get_password_hash("Admin123!"),
                # rol_id=admin_role.id,
                estado="Activo"
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            print(f"Usuario {admin_email} creado exitosamente con rol {admin_role.nombre} y contraseña 'Admin123!'.")
        else:
            # Asegurarse de que tenga el rol correcto
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
            # Asegurar que la contraseña cumpla los requisitos
            admin_user.password = get_password_hash("Admin123!")
            db.commit()
            print(f"El usuario {admin_email} ya existe. Se ha asegurado su rol de administrador y se ha actualizado su contraseña a 'Admin123!'.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
