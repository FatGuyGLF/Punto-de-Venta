import sqlite3

class Database:
    """
    Clase responsable de manejar la conexión y la estructura de la base de datos.
    Diseñada con una estructura limpia para un negocio local.
    """
    def __init__(self, dbPath="pos.db"):
        self.dbPath = dbPath
        self.createTables()

    def connect(self):
        """Crea y devuelve una nueva conexión a la base de datos."""
        return sqlite3.connect(self.dbPath)

    def createTables(self):
        """
        Contiene todo el esquema de la base de datos.
        Crea las tablas si no existen al iniciar la aplicación.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # --- TABLA DE USUARIOS ---
            # Almacena las credenciales y roles para el control de acceso.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    idUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    passwordHash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """)
            
            # --- TABLA DE CATEGORÍAS ---
            # Permite agrupar productos para una mejor organización y filtrado.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    idCategoria INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL
                )
            """)
            
            # --- TABLA DE PRODUCTOS ---
            # El inventario central de la tienda.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    idProducto INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigoBarras TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    precioVenta REAL NOT NULL,
                    costoCompra REAL DEFAULT 0,
                    stock INTEGER NOT NULL,
                    idCategoria INTEGER,
                    FOREIGN KEY (idCategoria) REFERENCES categorias(idCategoria)
                )
            """)

            # --- TABLAS DE OPERACIONES DE VENTA ---
            # Tabla principal que registra cada transacción.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    idVenta INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    descuento REAL DEFAULT 0,
                    totalVenta REAL NOT NULL,
                    metodoPago TEXT
                )
            """)
            
            # Tabla que detalla los productos incluidos en cada venta.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detallesVenta (
                    idDetalleVenta INTEGER PRIMARY KEY AUTOINCREMENT,
                    idVenta INTEGER NOT NULL,
                    idProducto INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precioUnitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (idVenta) REFERENCES ventas(idVenta),
                    FOREIGN KEY (idProducto) REFERENCES productos(idProducto)
                )
            """)

            # Registra los productos devueltos por los clientes.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devoluciones (
                    idDevolucion INTEGER PRIMARY KEY AUTOINCREMENT,
                    idVentaOriginal INTEGER NOT NULL,
                    idProducto INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    montoDevuelto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    FOREIGN KEY (idVentaOriginal) REFERENCES ventas(idVenta),
                    FOREIGN KEY (idProducto) REFERENCES productos(idProducto)
                )
            """)
            
            # --- TABLA DE GASTOS ---
            # Registra salidas de dinero no relacionadas con la compra de inventario.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos (
                    idGasto INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    monto REAL NOT NULL
                )
            """)
            
            conn.commit()